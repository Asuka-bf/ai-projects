"""
简化版数据导入脚本
分批处理，显示详细进度
"""

import json
import os
import sys
import hashlib
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def import_data(json_path: str, batch_size: int = 100):
    """导入数据到知识库"""
    from src.embedder import get_embedder
    import chromadb
    from chromadb.config import Settings

    # 加载数据
    print(f"加载数据: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    print(f"共 {len(qa_data)} 条数据")

    # 初始化 embedder
    print("加载向量化模型...")
    embedder = get_embedder()
    print("模型加载完成")

    # 初始化 ChromaDB
    vector_store_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_store_v2")
    os.makedirs(vector_store_dir, exist_ok=True)

    print(f"初始化向量数据库: {vector_store_dir}")
    client = chromadb.PersistentClient(
        path=vector_store_dir,
        settings=Settings(anonymized_telemetry=False)
    )

    # 删除旧集合
    try:
        client.delete_collection("qa_knowledge")
        print("已清除旧数据")
    except Exception:
        pass

    collection = client.create_collection(
        name="qa_knowledge",
        metadata={"hnsw:space": "cosine"}
    )

    # 分批导入
    total = len(qa_data)
    imported = 0
    start_time = time.time()

    print(f"\n开始导入（每批 {batch_size} 条）...")

    for i in range(0, total, batch_size):
        batch = qa_data[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        # 准备数据
        texts = []
        documents = []
        metadatas = []
        ids = []

        for j, qa in enumerate(batch):
            # 构建向量化文本
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

        # 生成向量
        print(f"  批次 {batch_num}/{total_batches}: 向量化 {len(texts)} 条...", end="", flush=True)
        embeddings = embedder.embed_texts(texts, show_progress=False)
        print(" 完成", flush=True)

        # 存入数据库
        print(f"  批次 {batch_num}/{total_batches}: 存入数据库...", end="", flush=True)
        collection.add(
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )
        print(" 完成", flush=True)

        imported += len(batch)
        elapsed = time.time() - start_time
        speed = imported / elapsed if elapsed > 0 else 0
        eta = (total - imported) / speed if speed > 0 else 0
        print(f"  进度: {imported}/{total} ({imported/total*100:.1f}%) | 速度: {speed:.1f} 条/秒 | 预计剩余: {eta:.0f} 秒", flush=True)

    # 统计
    print(f"\n{'='*50}")
    print(f"导入完成!")
    print(f"{'='*50}")
    print(f"总文档数: {collection.count()}")
    print(f"耗时: {time.time() - start_time:.1f} 秒")

    # 分类统计
    all_metas = collection.get()['metadatas']
    from collections import Counter
    cats = Counter(m.get('category', '其他') for m in all_metas)
    print(f"\n分类分布:")
    for cat, count in cats.most_common():
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="导入数据到知识库")
    parser.add_argument("--data", type=str, required=True, help="JSON 数据文件路径")
    parser.add_argument("--batch-size", type=int, default=100, help="批量大小")

    args = parser.parse_args()
    import_data(args.data, args.batch_size)
