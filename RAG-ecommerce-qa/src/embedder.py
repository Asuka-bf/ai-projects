"""
向量化模块 - 使用 BAAI/bge-small-zh-v1.5 模型
支持批量处理和缓存
"""

import os
import json
import hashlib
from typing import List, Optional, Union
from pathlib import Path

import numpy as np

# 导入 sentence_transformers，不可用时降级为简化向量
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("[Embedder] sentence_transformers 不可用，使用简化向量")


class Embedder:
    """使用 BGE 模型进行文本向量化"""

    DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"
    CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_store_v2", "embedding_cache")

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        batch_size: int = 32,
        use_cache: bool = True,
        device: Optional[str] = None
    ):
        """
        初始化向量化模型

        Args:
            model_name: HuggingFace 模型名称或路径
            batch_size: 批处理大小
            use_cache: 是否使用缓存
            device: 使用设备（cpu/cuda），None 时自动检测
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.use_cache = use_cache
        self.use_fallback = False

        # 加载模型（支持重试和镜像）
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            print(f"正在加载向量化模型: {model_name}")
            try:
                self.model = SentenceTransformer(model_name, device=device)
            except Exception as e:
                print(f"从默认源加载模型失败: {e}")
                print("尝试使用 HuggingFace 镜像...")
                os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                try:
                    self.model = SentenceTransformer(model_name, device=device)
                except Exception as e2:
                    print(f"从镜像加载模型失败: {e2}")
                    print("降级为简化向量")
                    self.use_fallback = True
                    self.model = None
            if not self.use_fallback:
                print(f"模型加载成功，设备: {self.model.device}")
        else:
            print("sentence_transformers 不可用，使用简化向量")
            self.use_fallback = True
            self.model = None

        # 设置缓存
        if use_cache:
            os.makedirs(self.CACHE_DIR, exist_ok=True)
            self.cache_file = os.path.join(self.CACHE_DIR, "embeddings_cache.json")
            self.cache = self._load_cache()
        else:
            self.cache = {}

    def _load_cache(self) -> dict:
        """从磁盘加载向量缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        """保存向量缓存到磁盘"""
        if self.use_cache and self.cache:
            try:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.cache, f)
            except Exception as e:
                print(f"Warning: Failed to save cache: {e}")

    def _get_cache_key(self, text: str) -> str:
        """生成文本的缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _simple_embed(self, text: str) -> np.ndarray:
        """简化向量化（基于 MD5 哈希，仅供调试）"""
        # 基于 MD5 哈希生成确定性伪向量
        import hashlib

        # 创建确定性的简单向量
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()

        # 转换为浮点数组并归一化
        emb = np.array([float(b) / 255.0 for b in hash_bytes], dtype=np.float32)

        # 填充或截断到 128 维
        target_dim = 128
        if len(emb) < target_dim:
            emb = np.pad(emb, (0, target_dim - len(emb)), 'constant')
        else:
            emb = emb[:target_dim]

        # L2 归一化
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm

        return emb

    def embed_texts(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        批量向量化文本

        Args:
            texts: 文本列表
            show_progress: 是否显示进度条

        Returns:
            向量数组
        """
        if not texts:
            return np.array([])

        # 模型不可用时使用简化向量
        if self.use_fallback:
            print(f"使用简化向量处理 {len(texts)} 条文本...")
            return np.array([self._simple_embed(t) for t in texts])

        # 检查缓存中已有的向量
        embeddings = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        if self.use_cache:
            for i, text in enumerate(texts):
                key = self._get_cache_key(text)
                if key in self.cache:
                    embeddings[i] = self.cache[key]
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(text)
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = texts

        # 对未缓存的文本生成向量
        if uncached_texts:
            print(f"正在生成 {len(uncached_texts)} 条文本的向量...")
            new_embeddings = self.model.encode(
                uncached_texts,
                batch_size=self.batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=True
            )

            # 更新缓存
            if self.use_cache:
                for idx, text, emb in zip(uncached_indices, uncached_texts, new_embeddings):
                    key = self._get_cache_key(text)
                    self.cache[key] = emb.tolist()
                self._save_cache()

            # 填充新向量
            for idx, emb in zip(uncached_indices, new_embeddings):
                embeddings[idx] = emb

        return np.array(embeddings)

    def embed_query(self, query: str) -> np.ndarray:
        """
        向量化单条查询文本

        Args:
            query: 查询文本

        Returns:
            向量数组
        """
        # 模型不可用时使用简化向量
        if self.use_fallback:
            return self._simple_embed(query)

        # BGE 模型查询端加前缀，提升检索精度
        if not query.startswith("为这个句子生成表示以用于检索相关文章："):
            query = "为这个句子生成表示以用于检索相关文章：" + query

        embedding = self.model.encode(
            [query],
            normalize_embeddings=True
        )
        return embedding[0]

    def get_dimension(self) -> int:
        """获取向量维度"""
        if self.use_fallback:
            return 128  # 简单向量化维度
        return self.model.get_sentence_embedding_dimension()


# 单例实例（复用）
_embedder_instance: Optional[Embedder] = None


def get_embedder(**kwargs) -> Embedder:
    """获取或创建单例向量化模型"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder(**kwargs)
    return _embedder_instance
