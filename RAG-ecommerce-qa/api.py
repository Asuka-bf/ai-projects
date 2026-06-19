"""
电商智能客服系统 - FastAPI 服务
基于 RAG 技术的电商智能客服问答系统
"""

import os
import json
import shutil
import hashlib
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from collections import Counter

# 加载 .env 环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass  # python-dotenv 未安装时忽略，直接用系统环境变量

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from src.document_parser import DocumentParser
from src.embedder import get_embedder

import chromadb
from chromadb.config import Settings
import httpx

# DeepSeek API 配置
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/anthropic")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

# 初始化 FastAPI 应用
app = FastAPI(
    title="电商智能客服系统",
    description="基于 RAG 技术的电商智能客服问答系统",
    version="2.0.0"
)

# 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), "vector_store_v2")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 检查 API Key 是否配置
if not DEEPSEEK_API_KEY:
    print("=" * 60)
    print("[Config] DEEPSEEK_API_KEY 未设置")
    print("  请复制 .env.example 为 .env 并填入你的 DeepSeek API Key")
    print("=" * 60)

# 初始化组件
document_parser = DocumentParser(chunk_size=500, chunk_overlap=50)

# 全局实例（懒加载）
_embedder = None

# 预设推荐问题
SUGGESTED_QUESTIONS = [
    "什么时候发货？",
    "快递费多少钱？",
    "怎么退货？",
    "可以开发票吗？",
    "有什么优惠活动？",
    "质量怎么样？",
    "可以换颜色吗？",
    "怎么使用优惠券？",
]

# 分类列表
CATEGORIES = [
    {"name": "全部", "icon": "📋", "description": "查看所有问题"},
    {"name": "物流配送", "icon": "🚚", "description": "发货、快递、运费相关"},
    {"name": "退换货", "icon": "🔄", "description": "退货、换货、退款相关"},
    {"name": "订单支付", "icon": "💰", "description": "下单、付款、价格相关"},
    {"name": "优惠活动", "icon": "🎁", "description": "优惠券、折扣、活动相关"},
    {"name": "产品咨询", "icon": "📦", "description": "质量、规格、产品相关"},
    {"name": "账户服务", "icon": "👤", "description": "发票、地址、备注相关"},
    {"name": "售前咨询", "icon": "💬", "description": "库存、有货、预售相关"},
    {"name": "售后服务", "icon": "🔧", "description": "破损、漏发、问题处理"},
]


def get_embedder_instance():
    """获取或初始化向量化模型"""
    global _embedder
    if _embedder is None:
        try:
            _embedder = get_embedder()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"向量模型加载失败: {str(e)}"
            )
    return _embedder


def get_chroma_client():
    """获取 ChromaDB 客户端"""
    return chromadb.PersistentClient(
        path=VECTOR_STORE_DIR,
        settings=Settings(anonymized_telemetry=False)
    )


def get_qa_collection():
    """获取核心知识库集合（8000条结构化Q&A）"""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="qa_knowledge",
        metadata={"hnsw:space": "cosine"}
    )


def get_doc_collection():
    """获取文档知识库集合（用户上传的文档）"""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="doc_knowledge",
        metadata={"hnsw:space": "cosine"}
    )


def get_related_questions(category: str, exclude_question: str, limit: int = 2) -> list:
    """
    获取同类别的推荐问题

    Args:
        category: 当前问题的分类（如"物流配送"）
        exclude_question: 排除当前问题（避免重复推荐）
        limit: 推荐几个问题

    Returns:
        推荐问题列表
    """
    try:
        qa_collection = get_qa_collection()

        # 查询同类别文档
        results = qa_collection.get(
            where={"category": category},
            limit=20
        )

        if results and results['metadatas']:
            # 提取问题列表，排除当前问题和太短的问题（少于4个字）
            questions = [
                m['question'] for m in results['metadatas']
                if m.get('question')
                and m['question'] != exclude_question
                and len(m['question']) >= 4  # 过滤掉太短的问题
            ]

            # 随机选择
            import random
            if len(questions) > limit:
                return random.sample(questions, limit)
            return questions[:limit]

        return []
    except Exception:
        return []


def get_collection():
    """获取默认知识库集合"""
    return get_qa_collection()


async def generate_answer_with_llm(question: str, context_docs: list) -> str:
    """
    调用 DeepSeek API 生成 RAG 回答

    Args:
        question: 用户问题
        context_docs: 检索到的相关文档列表

    Returns:
        LLM 生成的回答
    """
    # 构建上下文
    context_parts = []
    for i, doc in enumerate(context_docs[:3], 1):
        q = doc.get('question', '')
        a = doc.get('answer', '')
        context_parts.append(f"[参考{i}] 问题：{q}\n回答：{a}")

    context = "\n\n".join(context_parts)

    # 构建 prompt
    system_prompt = """你是一位专业的电商智能客服助手。请根据知识库中的参考信息，回答用户的问题。

要求：
1. 基于参考信息回答，不要编造信息
2. 回答要简洁、专业、友好
3. 如果参考信息中没有相关内容，请礼貌地说明并建议联系人工客服
4. 使用中文回答"""

    user_prompt = f"""参考信息：
{context}

用户问题：{question}

请根据以上参考信息回答用户的问题。"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{DEEPSEEK_API_BASE}/v1/messages",
                headers={
                    "x-api-key": DEEPSEEK_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": DEEPSEEK_MODEL,
                    "max_tokens": 300,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": user_prompt}
                    ]
                }
            )

            if response.status_code == 200:
                result = response.json()
                # 提取 text 类型的 content
                for item in result.get("content", []):
                    if item.get("type") == "text" and item.get("text"):
                        return item["text"].strip()
                return None
            else:
                print(f"DeepSeek API error: {response.status_code} - {response.text}")
                return None

    except Exception as e:
        print(f"DeepSeek API call failed: {e}")
        return None


# 数据模型
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3
    category: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    category: str


class SystemStats(BaseModel):
    total_documents: int
    categories: dict
    collection_name: str


class InitRequest(BaseModel):
    max_items: Optional[int] = None
    batch_size: Optional[int] = 64


# API 端点
@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端页面"""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>电商智能客服系统</h1><p>前端页面未找到</p>"


@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """
    智能问答接口

    根据用户问题检索知识库，返回最相关的答案
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    try:
        embedder = get_embedder_instance()

        # 问题向量化
        query_embedding = embedder.embed_query(request.question)

        # 构建分类过滤器
        where_filter = None
        if request.category and request.category != "全部":
            where_filter = {"category": request.category}

        SIMILARITY_THRESHOLD = 0.3
        sources = []

        # 第一步：优先从核心知识库（qa_knowledge）检索
        qa_collection = get_qa_collection()
        search_k = min(request.top_k * 3, 20)
        qa_results = qa_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=search_k,
            where=where_filter
        )

        if qa_results and qa_results['documents'] and qa_results['documents'][0]:
            for i in range(len(qa_results['documents'][0])):
                distance = qa_results['distances'][0][i] if qa_results['distances'] else 1.0
                score = 1 - (distance / 2)
               
                if score >= SIMILARITY_THRESHOLD: #相似度大于等于0.3才保留
                    meta = qa_results['metadatas'][0][i] if qa_results['metadatas'] else {}
                    sources.append({
                        'text': qa_results['documents'][0][i],
                        'score': round(score, 4),
                        'question': meta.get('question', ''),
                        'answer': meta.get('answer', ''),
                        'category': meta.get('category', '其他'),
                        'source': 'qa_knowledge',
                    })

        # 第二步：如果核心知识库结果不足，从文档知识库（doc_knowledge）补充
        if len(sources) < request.top_k:
            doc_collection = get_doc_collection()
            doc_results = doc_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=search_k,
            )

            if doc_results and doc_results['documents'] and doc_results['documents'][0]:
                for i in range(len(doc_results['documents'][0])):
                    distance = doc_results['distances'][0][i] if doc_results['distances'] else 1.0
                    score = 1 - (distance / 2)

                    if score >= SIMILARITY_THRESHOLD:
                        meta = doc_results['metadatas'][0][i] if doc_results['metadatas'] else {}
                        sources.append({
                            'text': doc_results['documents'][0][i],
                            'score': round(score, 4),
                            'question': meta.get('question', ''),
                            'answer': meta.get('answer', ''),
                            'category': meta.get('category', '文档上传'),
                            'source': 'doc_knowledge',
                        })

        # 按分数排序，取 top_k
        sources.sort(key=lambda x: x['score'], reverse=True)
        sources = sources[:request.top_k]

        # 生成回答
        if not sources:
            answer = "抱歉，没有找到与您问题相关的回答。请您换个方式描述问题，或者联系人工客服获取帮助。"
            detected_category = "其他"
        else:
            detected_category = sources[0]['category']

            # RAG: 调用 DeepSeek API 生成回答
            llm_answer = await generate_answer_with_llm(request.question, sources)

            if llm_answer:
                answer = llm_answer
            else:
                # LLM 调用失败，使用知识库模板
                answer = sources[0]['answer']

            # 获取同类别的推荐问题
            related_questions = get_related_questions(
                category=detected_category,
                exclude_question=request.question,
                limit=2
            )

            # 拼接推荐问题
            if related_questions:
                related_text = "\n".join([f"• {q}" for q in related_questions])
                answer += f"\n\n您可能还想问：\n{related_text}"

        return QueryResponse(
            answer=answer,
            sources=sources,
            category=detected_category
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@app.get("/categories")
async def get_categories():
    """获取所有分类"""
    try:
        qa_collection = get_qa_collection()
        all_metas = qa_collection.get()['metadatas']
        cat_counts = Counter(m.get('category', '其他') for m in all_metas)

        result = []
        for cat in CATEGORIES:
            count = cat_counts.get(cat['name'], 0) if cat['name'] != "全部" else sum(cat_counts.values())
            result.append({**cat, "count": count})

        return result
    except Exception as e:
        return CATEGORIES


@app.get("/suggest")
async def get_suggested_questions(category: Optional[str] = None):
    """获取推荐问题"""
    try:
        collection = get_qa_collection()

        # 获取随机问题
        where_filter = None
        if category and category != "全部":
            where_filter = {"category": category}

        results = collection.get(
            where=where_filter,
            limit=50
        )

        if results and results['metadatas']:
            questions = [m['question'] for m in results['metadatas'] if m.get('question')]
            # 随机选择问题
            import random
            if len(questions) > 8:
                suggested = random.sample(questions, 8)
            else:
                suggested = questions[:8]
            return {"questions": suggested, "category": category or "全部"}

        return {"questions": SUGGESTED_QUESTIONS, "category": category or "全部"}
    except Exception:
        return {"questions": SUGGESTED_QUESTIONS, "category": category or "全部"}


@app.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """获取系统统计信息"""
    try:
        qa_collection = get_qa_collection()
        doc_collection = get_doc_collection()

        qa_count = qa_collection.count()
        doc_count = doc_collection.count()

        all_metas = qa_collection.get()['metadatas']
        cat_counts = dict(Counter(m.get('category', '其他') for m in all_metas))

        return SystemStats(
            total_documents=qa_count + doc_count,
            categories=cat_counts,
            collection_name=f"qa_knowledge({qa_count}) + doc_knowledge({doc_count})"
        )
    except Exception as e:
        return SystemStats(
            total_documents=0,
            categories={},
            collection_name="qa_knowledge + doc_knowledge"
        )


@app.post("/init")
async def init_knowledge_base(request: InitRequest):
    """初始化知识库（从电商对话数据集导入）"""
    try:
        json_path = os.path.join(DATA_DIR, "ecommerce_qa.json")
        if not os.path.exists(json_path):
            raise HTTPException(
                status_code=404,
                detail="数据文件不存在，请先运行 data_loader.py 生成数据"
            )

        # 加载数据
        with open(json_path, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)

        if request.max_items:
            qa_data = qa_data[:request.max_items]

        embedder = get_embedder_instance()

        # 重置核心知识库集合
        client = get_chroma_client()
        try:
            client.delete_collection("qa_knowledge")
        except Exception:
            pass

        collection = client.create_collection(
            name="qa_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

        # 批量导入
        batch_size = request.batch_size or 64
        total = len(qa_data)
        imported = 0

        for i in range(0, total, batch_size):
            batch = qa_data[i:i + batch_size]

            texts = []
            documents = []
            metadatas = []
            ids = []

            for j, qa in enumerate(batch):
                # 构建向量化上下文
                context_parts = []
                if qa.get('conversation_history'):
                    recent = qa['conversation_history'][-3:]
                    context_parts.extend(recent)
                context_parts.append(qa['question'])
                embed_text = " ".join(context_parts)

                doc_text = f"问题：{qa['question']}\n回答：{qa['answer']}"

                texts.append(embed_text)
                documents.append(doc_text)
                metadatas.append({
                    "question": qa['question'],
                    "answer": qa['answer'],
                    "category": qa.get('category', '其他'),
                    "source": "ecommerce_dialogue"
                })
                unique_id = hashlib.md5(f"{i}_{j}_{embed_text}".encode()).hexdigest()
                ids.append(unique_id)

            embeddings = embedder.embed_texts(texts, show_progress=False)

            collection.add(
                documents=documents,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                ids=ids
            )

            imported += len(batch)

        return {
            "message": f"知识库初始化成功！导入了 {imported} 条数据",
            "total": imported
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")


@app.delete("/clear")
async def clear_knowledge_base(target: Optional[str] = Query(None, description="清空目标: qa=核心知识库, doc=文档知识库, 全部=清空所有")):
    """清空知识库"""
    try:
        client = get_chroma_client()

        if target == "qa":
            client.delete_collection("qa_knowledge")
            return {"message": "核心知识库已清空"}
        elif target == "doc":
            client.delete_collection("doc_knowledge")
            return {"message": "文档知识库已清空"}
        else:
            # 清空所有
            try:
                client.delete_collection("qa_knowledge")
            except Exception:
                pass
            try:
                client.delete_collection("doc_knowledge")
            except Exception:
                pass
            return {"message": "所有知识库已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档到知识库（支持 PDF, DOCX, TXT）"""
    allowed_extensions = {'.pdf', '.docx', '.doc', '.txt'}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}"
        )

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    try:
        parsed = document_parser.parse(file_path)
        embedder = get_embedder_instance()

        texts = [chunk['text'] for chunk in parsed['chunks']]
        embeddings = embedder.embed_texts(texts)

        metadatas = [
            {
                'source': file.filename,
                'chunk_index': chunk['index'],
                'question': chunk['text'][:100],
                'answer': chunk['text'],
                'category': '文档上传',
                'upload_time': datetime.now().isoformat()
            }
            for chunk in parsed['chunks']
        ]

        collection = get_doc_collection()
        ids = [hashlib.md5(f"{file.filename}:{i}:{t}".encode()).hexdigest() for i, t in enumerate(texts)]

        collection.upsert(
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )

        return {
            "message": f"文档 '{file.filename}' 上传成功",
            "chunks": parsed['chunk_count']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


# 挂载静态文件
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8084,
        reload=False,
        log_level="info"
    )
