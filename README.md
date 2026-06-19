# Operation — AI 运营内容中台

基于多 AI Agent 协作的智能内容运营平台，实现从**选题策划 → 文案生成 → 封面制作 → 多平台发布**的端到端自动化流水线。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn（异步） |
| 数据库 | Tortoise ORM（异步） + MySQL 8 + Aerich（迁移） |
| 认证鉴权 | PyJWT（HS256，无状态 Token） |
| AI 文本 | Coze（字节跳动扣子平台）— 选题 Bot + 文案 Bot |
| AI 图像 | DashScope（阿里云百炼）— Qwen-Image-2.0-Pro |
| 云存储 | Alibaba Cloud OSS（对象存储） |
| 自动化 | Playwright（浏览器自动化，小红书签名引擎） |
| 包管理 | uv |

## 功能概览

```
用户输入主题 → AI 拆解板块 + 生成标题 → AI 撰写文案 → AI 生成封面图 → 上传 OSS → 发布到小红书
```

| 步骤 | 功能 | 说明 |
|------|------|------|
| 1 | 智能选题 | 输入主题，Coze Bot 自动拆解板块并生成批量标题 |
| 2 | 文案编导 | 选中标题，Coze Bot 生成正文内容（可手动编辑） |
| 3 | 封面生成 | Qwen-Image 生成封面图，支持风格选择和文字嵌入 |
| 4 | 图片管理 | 本地上传 / AI 生成图 → OSS 云存储 |
| 5 | 多平台发布 | Playwright 自动签名 + Cookie 注入，发布到小红书 |
| 6 | 历史记录 | 发布记录、笔记链接追踪 |

## 项目结构

```
Operation/
├── main.py                    # FastAPI 启动入口
├── pyproject.toml             # 项目元数据 + 依赖
├── .env.example               # 环境变量模板
├── app/
│   ├── config.py              # 配置中心（数据库/JWT/OSS/AI）
│   ├── database.py            # Tortoise ORM 生命周期管理
│   ├── models/
│   │   └── __init__.py        # 8 张业务表 Model 定义
│   ├── routers/
│   │   ├── auth.py            # 登录 + JWT 鉴权
│   │   ├── create.py          # 核心业务（选题/文案/封面/发布）
│   │   └── xhs.py             # 小红书账号管理
│   ├── agent/
│   │   ├── coze_agent.py      # Coze 选题 + 文案 Agent
│   │   └── Qwen_agent.py      # Qwen 封面图生成 Agent
│   └── until/
│       ├── upload.py           # OSS 上传（本地/URL 双模式）
│       └── xhs_publish.py     # 小红书发布引擎（签名+发布）
└── migrations/                # Aerich 数据库迁移文件
```

## 快速开始

### 1. 环境要求

- Python >= 3.10
- MySQL 8
- [uv](https://github.com/astral-sh/uv)（Python 包管理）
- Chrome 浏览器（Playwright 签名引擎依赖）

### 2. 安装

```bash
git clone <repo-url>
cd Operation

# 安装依赖
uv sync

# 复制环境变量模板
cp .env.example .env
# 编辑 .env，填入真实配置

# 安装 Playwright 浏览器
uv run playwright install chromium
```

### 3. 数据库

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS \`bf-operation\` CHARACTER SET utf8mb4;"
uv run aerich upgrade
```

### 4. 启动

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API 文档自动生成：http://localhost:8000/docs

## 环境变量

| 变量 | 说明 |
|------|------|
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | MySQL 连接 |
| `JWT_SECRET` | JWT 签名密钥 |
| `COZE_TOKEN` | Coze 平台 Personal Access Token |
| `BOT_ID_TOPIC` / `BOT_ID_CONCENT` | 选题 / 文案机器人 ID |
| `QWEN_KEY` | 阿里云百炼 API Key |
| `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET` | OSS 凭证 |
| `OSS_REGION` / `OSS_BUCKET` / `OSS_ENDPOINT` | OSS 存储桶配置 |

## 数据库表

| 表 | 说明 |
|----|------|
| `t_users` | 用户表 |
| `t_sections` | 板块表（AI 生成的主题分组） |
| `t_titles` | 标题表（含正文内容与状态） |
| `t_title_images` | 图片表（封面图 / 正文图） |
| `t_publish_records` | 发布记录表 |
| `t_publish_images` | 发布图片关联表 |
| `t_xhs_accounts` | 小红书账号 Cookie 管理 |
| `t_style` | AI 风格配置 |
| `t_models` | AI 模型配置 |

## 设计要点

- **多 AI 平台协作**：Coze（文本）+ Qwen（图像）异构 AI 平台流水线串联，选题 → 文案 → 封面三步自动化
- **异步全链路**：FastAPI + Tortoise ORM 全链路 async/await，数据库操作不阻塞事件循环
- **子进程隔离**：Playwright 签名引擎通过 `subprocess` 子进程运行，解决 greenlet 与 asyncio 事件循环在 Windows 上的冲突
- **双模式上传**：本地文件直接上传 + URL 转发上传（AI 生成的图不落盘，内存直传 OSS）
- **结果文件 IPC**：子进程通过 `--output` 临时文件返回 JSON，避免 Playwright 浏览器日志污染 stdout
