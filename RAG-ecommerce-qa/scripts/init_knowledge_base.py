"""
知识库初始化脚本
将电商 Q&A 数据导入向量数据库
"""

import json
import os
import sys
import hashlib
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def load_qa_data(json_path: str) -> list:
    """加载 Q&A 数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def init_knowledge_base(
    json_path: str = None,
    batch_size: int = 64,
    max_items: int = None
):
    """
    初始化知识库

    Args:
        json_path: Q&A JSON 文件路径
        batch_size: 批量处理大小
        max_items: 最大导入数量（调试用）
    """
    from src.embedder import get_embedder
    import chromadb
    from chromadb.config import Settings

    # 默认路径
    if json_path is None:
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ecommerce_qa.json")

    if not os.path.exists(json_path):
        print(f"错误: 数据文件不存在: {json_path}")
        print("请先运行 data_loader.py 生成数据")
        return

    # 加载数据
    print(f"正在加载数据: {json_path}")
    qa_data = load_qa_data(json_path)
    if max_items:
        qa_data = qa_data[:max_items]
    print(f"加载了 {len(qa_data)} 条 Q&A 数据")

    # 初始化 embedder
    print("正在加载向量模型...")
    embedder = get_embedder()

    # 初始化 ChromaDB
    vector_store_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_store_v2")
    os.makedirs(vector_store_dir, exist_ok=True)

    print(f"正在初始化向量数据库: {vector_store_dir}")
    client = chromadb.PersistentClient(
        path=vector_store_dir,
        settings=Settings(anonymized_telemetry=False)
    )

    # 删除旧集合，重新创建
    try:
        client.delete_collection("qa_knowledge")
        print("已清除旧的知识库数据")
    except Exception:
        pass

    collection = client.create_collection(
        name="qa_knowledge",
        metadata={"hnsw:space": "cosine"}
    )

    # 批量处理
    total = len(qa_data)
    processed = 0

    print(f"\n开始导入数据（每批 {batch_size} 条）...")

    for i in range(0, total, batch_size):
        batch = qa_data[i:i + batch_size]

        # 准备数据
        texts = []       # 用于向量化的文本（问题 + 对话历史）
        documents = []   # 存储的文档（完整 Q&A）
        metadatas = []
        ids = []

        for j, qa in enumerate(batch):
            # 向量化文本：问题 + 最近几轮对话历史
            context_parts = []
            if qa.get('conversation_history'):
                # 只取最近3轮对话作为上下文
                recent = qa['conversation_history'][-3:]
                context_parts.extend(recent)
            context_parts.append(qa['question'])
            embed_text = " ".join(context_parts)

            # 存储文档：包含问题、答案、分类
            doc_text = f"问题：{qa['question']}\n回答：{qa['answer']}"

            texts.append(embed_text)
            documents.append(doc_text)
            metadatas.append({
                "question": qa['question'],
                "answer": qa['answer'],
                "category": qa.get('category', '其他'),
                "source": "ecommerce_dialogue"
            })
            # Use index + hash to ensure uniqueness
            unique_id = hashlib.md5(f"{i}_{j}_{embed_text}".encode()).hexdigest()
            ids.append(unique_id)

        # 生成向量
        embeddings = embedder.embed_texts(texts, show_progress=False)

        # 存入 ChromaDB
        collection.add(
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )

        processed += len(batch)
        pct = processed / total * 100
        print(f"  进度: {processed}/{total} ({pct:.1f}%)")

    # 统计
    print(f"\n{'='*50}")
    print(f"知识库初始化完成!")
    print(f"{'='*50}")
    print(f"总文档数: {collection.count()}")
    print(f"存储位置: {vector_store_dir}")

    # 分类统计
    all_metas = collection.get()['metadatas']
    from collections import Counter
    cats = Counter(m.get('category', '未知') for m in all_metas)
    print(f"\n分类分布:")
    for cat, count in cats.most_common():
        print(f"  {cat}: {count}")

    print(f"\n初始化完成，启动 api.py 即可使用")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="初始化电商客服知识库")
    parser.add_argument("--data", type=str, help="Q&A JSON 文件路径")
    parser.add_argument("--batch-size", type=int, default=64, help="批量大小")
    parser.add_argument("--max-items", type=int, help="最大导入数量（调试用）")

    args = parser.parse_args()

    init_knowledge_base(
        json_path=args.data,
        batch_size=args.batch_size,
        max_items=args.max_items
    )
