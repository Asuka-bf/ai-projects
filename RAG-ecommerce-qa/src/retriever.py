"""
检索生成模块 - 基于 HuggingFace 本地模型
支持流式输出和自定义 prompt

当前 api.py 使用 ChromaDB + DeepSeek API，不再依赖此模块。
保留此文件供本地推理场景使用。
"""

import os
from typing import List, Dict, Any, Optional, Generator
from threading import Lock

from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
import torch
from threading import Thread

from .embedder import get_embedder
from .vector_store import get_vector_store


class Retriever:
    """RAG 检索器：向量检索 + LLM 生成"""

    DEFAULT_MODEL = "Qwen/Qwen1.5-1.8B-Chat"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        top_k: int = 3,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        device: Optional[str] = None
    ):
        self.model_name = model_name
        self.top_k = top_k
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

        # 自动检测设备
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # 加载组件
        print("Loading retrieval components...")
        self.embedder = get_embedder()
        self.vector_store = get_vector_store()

        # 加载 LLM
        print(f"Loading generation model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )

        if self.device == "cpu":
            self.model = self.model.to("cpu")

        self.model.eval()
        print(f"Generation model loaded on {self.device}")

        # Prompt template
        self.prompt_template = """基于以下参考信息回答用户的问题。如果参考信息中没有相关内容，请说明你无法根据提供的信息回答。

参考信息：
{context}

用户问题：{question}

回答："""

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """检索相关文档"""
        k = top_k or self.top_k

        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, top_k=k)

        return results

    def generate(
        self,
        question: str,
        context_docs: List[Dict[str, Any]],
        stream: bool = False
    ) -> Any:
        """基于检索到的上下文生成回答"""
        # 构建上下文
        context = "\n\n".join([
            f"[文档{i+1}] {doc['text']}"
            for i, doc in enumerate(context_docs)
        ])

        # Build prompt
        prompt = self.prompt_template.format(
            context=context,
            question=question
        )

        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")
        if self.device == "cuda":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        if stream:
            return self._generate_stream(inputs)
        else:
            return self._generate_sync(inputs)

    def _generate_sync(self, inputs: Dict) -> str:
        """同步生成"""
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1
            )

        # Decode only the new tokens
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        return response.strip()

    def _generate_stream(self, inputs: Dict) -> Generator[str, None, None]:
        """流式生成"""
        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        generation_kwargs = {
            **inputs,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "do_sample": True,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
            "streamer": streamer
        }

        # Start generation in a separate thread
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        # Yield tokens
        for text in streamer:
            yield text

    def answer(
        self,
        question: str,
        top_k: Optional[int] = None,
        stream: bool = False
    ) -> Any:
        """完整 RAG 流程：检索 + 生成"""
        # 检索
        context_docs = self.retrieve(question, top_k)

        if stream:
            return {
                'answer': self.generate(question, context_docs, stream=True),
                'sources': context_docs
            }
        else:
            answer = self.generate(question, context_docs, stream=False)
            return {
                'answer': answer,
                'sources': context_docs
            }


# 单例
_retriever_instance: Optional[Retriever] = None


def get_retriever(**kwargs) -> Retriever:
    """获取或创建 Retriever 单例"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever(**kwargs)
    return _retriever_instance
