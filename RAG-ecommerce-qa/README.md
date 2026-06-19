# 🛒 电商智能客服系统

基于 **RAG（检索增强生成）** 技术的电商智能客服问答系统，使用 DeepSeek 大模型 + BGE 向量化 + ChromaDB 向量数据库。

## ✨ 核心功能

- 🔍 **RAG 检索增强生成** — 先检索相关知识，再结合大模型生成准确回答
- 📄 **文档上传** — 支持 PDF / DOCX / TXT 格式，自动解析并入库
- 🏷️ **问题分类** — 自动识别 9 大类问题（物流、退换货、支付、促销、商品等）
- 💡 **推荐问题** — 预设常见问题，一键提问
- 🎨 **电商风格 UI** — 原生 HTML/CSS/JS，绿色简洁风格

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Python 3.10 |
| 向量化模型 | BAAI/bge-small-zh-v1.5 |
| 向量数据库 | ChromaDB |
| 大语言模型 | DeepSeek V4 Pro（API） |
| 前端 | 原生 HTML/CSS/JS |
| 文档解析 | PyPDF2 + python-docx |

## 📁 项目结构

```
RAG/
├── api.py                     # 主 API 服务器（入口）
├── requirements.txt           # Python 依赖
├── README.md                  # 项目说明
│
├── docs/                      # 📚 文档
│   ├── RAG技术详解.md
│   ├── 三大核心流程详解.md
│   ├── 技术总结-答辩版.md
│   └── 用户手册.txt
│
├── scripts/                   # 🔧 数据处理脚本
│   ├── data_loader.py         # 电商对话数据集预处理
│   ├── import_data.py         # 通用数据导入 ChromaDB
│   ├── init_knowledge_base.py # 知识库初始化
│   ├── process_brand_data.py  # 品牌数据解析
│   └── process_custom_data.py # 自定义对话数据解析
│
├── src/                       # 🧠 核心模块
│   ├── document_parser.py     # 文档解析（PDF/DOCX/TXT）
│   ├── embedder.py            # BGE 文本向量化
│   ├── vector_store.py        # ChromaDB 向量存储封装
│   └── retriever.py           # RAG 检索生成管线
│
├── data/                      # 📊 知识库数据
│   └── *.json, *.txt
│
└── static/                    # 🎨 前端页面
    └── index.html
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- [Anaconda](https://www.anaconda.com/)（推荐使用 py310 环境）

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/仓库名.git
cd 仓库名

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env 文件，填入你的 DeepSeek API Key
```

### 启动

```bash
# Windows
set HF_HUB_OFFLINE=1
python api.py

# 访问 http://localhost:8084
```

## 📡 API 接口

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/` | 前端页面 |
| POST | `/query` | RAG 问答 |
| GET | `/categories` | 获取问题分类 |
| GET | `/suggest` | 推荐问题 |
| GET | `/stats` | 系统统计 |
| POST | `/init` | 初始化知识库 |
| POST | `/upload` | 上传文档 |
| DELETE | `/clear` | 清空知识库 |

## 🔄 数据处理流程

```
原始数据 → data_loader.py → JSON 数据集
                              ↓
                    init_knowledge_base.py
                              ↓
                    ChromaDB 向量数据库
                              ↓
               api.py（RAG 检索 + DeepSeek 生成）
                              ↓
                        前端问答界面
```

## 📄 License

MIT License
