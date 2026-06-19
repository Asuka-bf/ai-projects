# 电商智能客服系统

## 项目简介
基于 RAG 技术的电商智能客服系统，使用 DeepSeek 大模型 + BGE 向量化 + ChromaDB 向量数据库。

## 技术栈
- **后端**: FastAPI + Python 3.10
- **向量化**: BAAI/bge-small-zh-v1.5
- **向量数据库**: ChromaDB
- **大模型**: DeepSeek V4 Pro（API）
- **前端**: 原生 HTML/CSS/JS

## 启动方式
```cmd
cd d:\AIProject\RAG
set HF_HUB_OFFLINE=1
python api.py
```

访问: http://localhost:8084

## 项目结构
```
RAG/
├── api.py                  # 主 API 服务器
├── data_loader.py          # 数据处理脚本
├── init_knowledge_base.py  # 知识库初始化
├── data/                   # 数据目录
├── src/                    # 核心模块
│   ├── document_parser.py  # 文档解析
│   ├── embedder.py         # 向量化
│   ├── vector_store.py     # 向量存储
│   └── retriever.py        # 检索生成
├── static/                 # 前端页面
└── vector_store_v2/        # 向量库
```

## 核心功能
1. RAG 检索增强生成
2. 文档上传（PDF/DOCX/TXT）
3. 问题分类（9 大类）
4. 推荐问题
5. 电商风格 UI

## 环境要求
- Python 3.10（Anaconda py310）
- 依赖: fastapi, uvicorn, sentence-transformers, chromadb, httpx 等
