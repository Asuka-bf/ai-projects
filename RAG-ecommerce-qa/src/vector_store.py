"""
向量存储模块 - 基于 ChromaDB 的向量存储
支持持久化存储和元数据过滤

当前 api.py 直接调用 chromadb 库，此模块保留供独立检索场景使用。
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
import numpy as np


class VectorStore:
    """ChromaDB 向量存储"""

    DEFAULT_COLLECTION = "knowledge_base"

    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = DEFAULT_COLLECTION
    ):
        """
        初始化向量存储

        Args:
            persist_directory: 持久化存储目录
            collection_name: 集合名称
        """
        if persist_directory is None:
            persist_directory = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "vector_store"
            )

        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # 确保目录存在
        os.makedirs(persist_directory, exist_ok=True)

        # 初始化客户端和集合
        self._init_client()

        print(f"向量存储初始化完成: {persist_directory}")
        print(f"集合 '{collection_name}' 包含 {self.collection.count()} 条文档")

    def _init_client(self):
        """初始化 ChromaDB 客户端和集合"""
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(
        self,
        texts: List[str],
        embeddings: np.ndarray,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        添加文档到向量存储

        Args:
            texts: 文本列表
            embeddings: 向量数组
            metadatas: 元数据列表（可选）
            ids: 文档 ID 列表（可选）

        Returns:
            文档 ID 列表
        """
        if not texts:
            return []

        # 生成 ID（如果未提供）
        if ids is None:
            import hashlib
            ids = [hashlib.md5(t.encode()).hexdigest() for t in texts]

        # 准备元数据
        if metadatas is None:
            metadatas = [{} for _ in texts]

        # 转换向量格式
        embeddings_list = embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings

        # 批量添加到集合
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            end = min(i + batch_size, len(texts))
            try:
                self.collection.add(
                    documents=texts[i:end],
                    embeddings=embeddings_list[i:end],
                    metadatas=metadatas[i:end],
                    ids=ids[i:end]
                )
            except Exception:
                self._reinit_client()
                self.collection.add(
                    documents=texts[i:end],
                    embeddings=embeddings_list[i:end],
                    metadatas=metadatas[i:end],
                    ids=ids[i:end]
                )

        print(f"已添加 {len(texts)} 条文档到向量存储")
        return ids

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文档

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filter_dict: 元数据过滤器（可选）

        Returns:
            搜索结果列表（包含文本、分数、元数据）
        """
        # 转换向量格式
        query_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding

        # 执行搜索（支持重试）
        try:
            results = self.collection.query(
                query_embeddings=[query_list],
                n_results=top_k,
                where=filter_dict
            )
        except Exception:
            self._reinit_client()
            results = self.collection.query(
                query_embeddings=[query_list],
                n_results=top_k,
                where=filter_dict
            )

        # 格式化结果
        formatted_results = []
        if results and results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                result = {
                    'text': results['documents'][0][i],
                    'score': 1 - results['distances'][0][i],  # 距离转相似度
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'id': results['ids'][0][i] if results['ids'] else None
                }
                formatted_results.append(result)

        return formatted_results

    def delete_collection(self):
        """删除当前集合"""
        self.client.delete_collection(self.collection_name)
        print(f"已删除集合: {self.collection_name}")

    def get_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            count = self.collection.count()
        except Exception:
            # 客户端关闭时重新初始化
            self._reinit_client()
            count = self.collection.count()
        return {
            'collection_name': self.collection_name,
            'document_count': count,
            'persist_directory': self.persist_directory
        }

    def _reinit_client(self):
        """重新初始化 ChromaDB 客户端"""
        try:
            if hasattr(self, 'client'):
                del self.client
        except Exception:
            pass
        self._init_client()

    def clear(self):
        """清空集合中的所有文档"""
        self.delete_collection()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print("集合已清空")


# 单例实例
_vector_store_instance: Optional[VectorStore] = None


def get_vector_store(**kwargs) -> VectorStore:
    """获取或创建单例向量存储实例"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(**kwargs)
    return _vector_store_instance


def reset_vector_store():
    """重置单例实例（用于测试或重新初始化）"""
    global _vector_store_instance
    _vector_store_instance = None
