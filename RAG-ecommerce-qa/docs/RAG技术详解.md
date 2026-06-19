# RAG 技术详解 — 向量化、向量数据库、检索增强生成

---

## 一、向量化技术（embedder.py）

### 1.1 什么是向量化？为什么需要它？

**一句话**：把文字变成一组数字，让计算机能"理解"文字的含义。

**生活类比**：想象你在一个图书馆找书。如果只按书名精确匹配，搜"做菜"只能找到书名里有"做菜"的书。但如果每本书都被翻译成了一组"特征数字"（比如：烹饪程度=0.9、文学程度=0.1、科技程度=0.05），你就能找到"烹饪程度高"的所有书，包括《家常菜谱》《烘焙入门》等——即使书名里没有"做菜"。

**这就是向量化的意义**：让"语义相近的文字"变成"数字相近的向量"。

```
文字: "发货"    → 向量: [0.8, 0.1, 0.9, 0.05, ...] (512个数字)
文字: "快递"    → 向量: [0.79, 0.12, 0.88, 0.06, ...]  ← 数字很接近！
文字: "天气"    → 向量: [0.1, 0.9, 0.05, 0.8, ...]  ← 数字差很远
```

### 1.2 BGE 模型是怎么工作的？

代码位置：`src/embedder.py` 第 23-71 行

```python
class Embedder:
    DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"

    def __init__(self, model_name=DEFAULT_MODEL, ...):
        self.model = SentenceTransformer(model_name, device=device)
```

**BGE 模型是什么？**

BGE（BAAI General Embedding）是智源研究院训练的一个"文字翻译器"，它能把一段中文文字翻译成 **512 个数字组成的向量**。

**类比**：BGE 就像一个翻译官，你给它一句中文，它输出 512 个数字。这个翻译官经过大量训练，学会了"意思相近的话 → 数字相近的向量"。

**关键参数**：

| 参数 | 值 | 含义 |
|------|------|------|
| 模型 | bge-small-zh-v1.5 | 小模型，24M 参数，速度快 |
| 向量维度 | 512 维 | 每个文字被翻译成 512 个数字 |
| 归一化 | L2 归一化 | 把向量长度标准化为 1，方便计算相似度 |

### 1.3 文档向量化 vs 查询向化（最关键的细节）

代码位置：`src/embedder.py` 第 189-211 行

```python
def embed_query(self, query: str) -> np.ndarray:
    # BGE 模型查询端加前缀，提升检索精度
    if not query.startswith("为这个句子生成表示以用于检索相关文章："):
        query = "为这个句子生成表示以用于检索相关文章：" + query

    embedding = self.model.encode([query], normalize_embeddings=True)
    return embedding[0]
```

**为什么查询要加前缀，文档不加？**

这是 BGE 模型的设计约定。**类比**：

想象你在一个双语会议上：
- **文档**就像是预先准备好的演讲稿（用"正式语言"写）
- **查询**就像是现场提问（用"口语"写）

为了让"口语问题"能匹配到"正式演讲稿"，需要给问题加一个"翻译前缀"，把它从"口语空间"转换到"正式空间"。

```
文档编码:  "48小时内发货"           → 直接编码 → 向量A
查询编码:  "什么时候发货？"         → 加前缀后编码 → 向量B
向量A 和 向量B 在同一语义空间，距离很近 ✓
```

**如果不加前缀会怎样？** 查询向量和文档向量在不同的语义空间，相似度计算会不准确，检索效果变差。

### 1.4 缓存机制（为什么需要缓存？）

代码位置：`src/embedder.py` 第 149-187 行

```python
def embed_texts(self, texts, show_progress=True):
    # 检查缓存中已有的向量
    for i, text in enumerate(texts):
        key = self._get_cache_key(text)  # MD5哈希作为缓存键
        if key in self.cache:
            embeddings[i] = self.cache[key]  # 命中缓存，直接用
        else:
            uncached_texts.append(text)  # 没缓存，需要计算

    # 只对没缓存的调用模型
    if uncached_texts:
        new_embeddings = self.model.encode(uncached_texts, ...)
        # 存入缓存
        self.cache[key] = emb.tolist()
```

**类比**：就像你做数学题，第一遍算 123×456=56088，写在草稿纸上。下次再遇到 123×456，直接看草稿纸，不用重新算。

**为什么重要？** 向量化是最耗时的操作（尤其在 CPU 上）。8000 条文本，每条都要过一遍神经网络。有了缓存，第二次启动时直接从磁盘读取，几秒就完成。

### 1.5 降级方案（优雅降级）

代码位置：`src/embedder.py` 第 104-128 行

```python
def _simple_embed(self, text: str) -> np.ndarray:
    """简单向量化备选方案（基于字符特征）"""
    hash_obj = hashlib.md5(text.encode('utf-8'))
    hash_bytes = hash_obj.digest()
    emb = np.array([float(b) / 255.0 for b in hash_bytes], dtype=np.float32)
    # 填充到 128 维，L2 归一化
    ...
```

**这是什么？** 如果 BGE 模型加载失败（网络问题、内存不够），系统不会崩溃，而是用 MD5 哈希生成一个"伪向量"。

**类比**：就像汽车爆胎后换上备胎——能开，但不舒适。伪向量没有语义理解能力，检索精度很低，但至少系统不会报错。

---

## 二、向量数据库（vector_store.py）

### 2.1 什么是向量数据库？为什么不用传统数据库？

**传统数据库**（如 MySQL）：

```sql
SELECT * FROM documents WHERE content LIKE '%发货%'
-- 只能找到"文字完全包含发货"的记录
-- 找不到"快递""物流"等语义相近的记录
```

**向量数据库**（如 ChromaDB）：

```
查询: "发货" → 向量: [0.8, 0.1, 0.9, ...]
搜索: 找到向量距离最近的 Top-K 条记录
→ 能找到"快递""物流""配送"等语义相近的记录
```

**类比**：
- 传统数据库 = 按书名精确搜索的图书馆系统
- 向量数据库 = 按"内容相似度"搜索的图书馆系统

### 2.2 ChromaDB 初始化

代码位置：`src/vector_store.py` 第 50-62 行

```python
def _init_client(self):
    self.client = chromadb.PersistentClient(
        path=self.persist_directory,           # 数据存在本地磁盘
        settings=Settings(anonymized_telemetry=False)
    )
    self.collection = self.client.get_or_create_collection(
        name=self.collection_name,
        metadata={"hnsw:space": "cosine"}      # 使用余弦距离
    )
```

**关键概念**：

| 概念 | 解释 | 类比 |
|------|------|------|
| `PersistentClient` | 数据持久化到磁盘 | 图书馆的实体建筑，书不会消失 |
| `collection` | 一个集合，存放相关文档 | 图书馆的一个楼层（如"科技层"） |
| `hnsw:space: cosine` | 使用 HNSW 索引 + 余弦距离 | 图书馆的分类索引系统 |

### 2.3 HNSW 索引（核心算法）

**什么是 HNSW？**

HNSW（Hierarchical Navigable Small World）是一种高效的向量搜索算法。

**类比**：想象你要在一个有 8000 本书的图书馆里找"最像《家常菜谱》的 5 本书"。

**暴力搜索**：把 8000 本书逐本和《家常菜谱》比较 → 慢，O(n) 复杂度

**HNSW 搜索**：

1. 图书馆的书被组织成"多层地图"
2. 最高层只有几本"代表书"，你先在顶层快速定位到大致区域
3. 然后逐层向下，每层都更精确
4. 最终在最底层找到最相似的 5 本书

```
第3层:  [科技代表]  [美食代表]  [文学代表]     ← 粗定位
              ↓
第2层:  [中餐] [西餐] [烘焙] [日料]           ← 中定位
              ↓
第1层:  [家常菜] [川菜] [粤菜] [炖菜] [炒菜]  ← 精定位
```

时间复杂度：**O(log n)**，比暴力搜索快很多。

### 2.4 添加文档

代码位置：`src/vector_store.py` 第 64-119 行

```python
def add_documents(self, texts, embeddings, metadatas=None, ids=None):
    # 生成 ID（如果未提供）
    if ids is None:
        ids = [hashlib.md5(t.encode()).hexdigest() for t in texts]

    # 批量添加到集合
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        self.collection.add(
            documents=texts[i:end],      # 原始文本
            embeddings=embeddings_list[i:end],  # 向量
            metadatas=metadatas[i:end],  # 元数据（分类、来源等）
            ids=ids[i:end]               # 唯一标识
        )
```

**每条文档存了什么？**

```
一条文档 = {
    id: "5e014a63f4602160a9efcd447b5dcf9c",  ← MD5哈希，唯一标识
    document: "问题：什么时候发货？\n回答：48小时内发货",  ← 原始文本
    embedding: [0.8, 0.1, 0.9, ...],          ← 512维向量
    metadata: {                                ← 附加信息
        "question": "什么时候发货？",
        "answer": "48小时内发货",
        "category": "物流配送",
        "source": "ecommerce_dialogue"
    }
}
```

**为什么要分批（batch_size=100）？** 避免一次写入太多数据导致内存溢出或 ChromaDB 报错。

### 2.5 相似度搜索

代码位置：`src/vector_store.py` 第 121-168 行

```python
def search(self, query_embedding, top_k=5, filter_dict=None):
    results = self.collection.query(
        query_embeddings=[query_list],  # 查询向量
        n_results=top_k,                # 返回前5个最相似的
        where=filter_dict               # 可选的元数据过滤
    )

    # 格式化结果
    for i in range(len(results['documents'][0])):
        result = {
            'text': results['documents'][0][i],
            'score': 1 - results['distances'][0][i],  # 距离转相似度
            'metadata': results['metadatas'][0][i],
        }
```

**距离 vs 相似度**：

```
余弦距离 (distance):  0 = 完全相同，2 = 完全相反
余弦相似度 (score):   1 - distance/2 → 范围 [-1, 1]
  - 1.0 = 完全相同
  - 0.0 = 完全无关
  - -1.0 = 完全相反
```

**类比**：两个人面对面站着，夹角越小（距离越小），方向越一致（相似度越高）。

---

## 三、RAG 检索增强生成（完整流程）

### 3.1 什么是 RAG？

RAG = **R**etrieval（检索） + **A**ugmented（增强） + **G**eneration（生成）

**问题**：大语言模型（如 DeepSeek）有两个致命缺陷：

1. **知识截止日期**：它只知道训练数据里的内容，不知道你公司的退货政策
2. **幻觉**：它会编造看似合理但错误的答案

**解决方案**：不让 LLM 凭空回答，先从知识库找到真实信息，再让 LLM 基于这些信息回答。

**类比**：
- **不用 RAG**：问一个路人"你们公司退货政策是什么？" → 他瞎猜
- **用 RAG**：先查公司手册找到退货政策，再让路人基于手册回答 → 准确

### 3.2 完整流程（结合代码）

用一个完整的例子走一遍：

```
用户输入: "怎么退货？"
```

#### 第一步：检索（Retrieval）

代码位置：`api.py` 第 267-314 行

```python
# ① 问题向量化
query_embedding = embedder.embed_query("怎么退货？")
# → "为这个句子生成表示以用于检索相关文章：怎么退货？"
# → BGE模型 → [0.78, 0.15, 0.92, ...] (512个数字)

# ② 向量检索（优先查 qa_knowledge）
qa_results = qa_collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=6,  # top_k * 3 = 3 * 3 = 6
)

# ③ 过滤结果（相似度 >= 0.3 才保留）
for i in range(len(qa_results['documents'][0])):
    distance = qa_results['distances'][0][i]
    score = 1 - (distance / 2)  # 距离转相似度
    if score >= 0.3:  # 阈值过滤
        sources.append({...})

# ④ 如果 qa_knowledge 结果不足，补充 doc_knowledge
if len(sources) < 3:
    doc_results = doc_collection.query(...)
```

**此时检索到的内容**：

```
[
  {text: "问题：怎么退货？\n回答：收到商品7天内可申请退货...", score: 0.95, category: "退换货"},
  {text: "问题：退款多久到账？\n回答：3-5个工作日...", score: 0.72, category: "退换货"},
  {text: "问题：可以换货吗？\n回答：可以，联系客服...", score: 0.65, category: "退换货"}
]
```

#### 第二步：增强（Augmented）

代码位置：`api.py` 第 147-170 行

```python
# 构建上下文
context_parts = []
for i, doc in enumerate(context_docs[:3], 1):
    q = doc.get('question', '')
    a = doc.get('answer', '')
    context_parts.append(f"[参考{i}] 问题：{q}\n回答：{a}")

context = "\n\n".join(context_parts)

# 构建 prompt
user_prompt = f"""参考信息：
{context}

用户问题：怎么退货？

请根据以上参考信息回答用户的问题。"""
```

**此时发给 LLM 的完整 Prompt**：

```
系统: 你是一位专业的电商智能客服助手。请根据知识库中的参考信息，回答用户的问题。
      要求：1. 基于参考信息回答，不要编造信息
            2. 回答要简洁、专业、友好
            3. 如果参考信息中没有相关内容，请礼貌地说明并建议联系人工客服
            4. 使用中文回答

用户: 参考信息：
      [参考1] 问题：怎么退货？ 回答：收到商品7天内可申请退货，需保持商品完好...
      [参考2] 问题：退款多久到账？ 回答：3-5个工作日内原路返回...
      [参考3] 问题：可以换货吗？ 回答：可以，联系客服办理...

      用户问题：怎么退货？
      请根据以上参考信息回答用户的问题。
```

#### 第三步：生成（Generation）

代码位置：`api.py` 第 172-204 行

```python
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(
        f"{DEEPSEEK_API_BASE}/v1/messages",
        json={
            "model": "deepseek-v4-pro",
            "max_tokens": 300,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
    )
```

**DeepSeek 的回答**：

```
"亲，收到商品后7天内可以申请退货哦~ 请保持商品完好，联系客服即可办理。
  退款将在3-5个工作日内原路返回。如果需要换货，也可以联系客服处理~"
```

#### 第四步：返回结果

代码位置：`api.py` 第 340-344 行

```python
return QueryResponse(
    answer=answer,        # LLM生成的自然语言回答
    sources=sources,      # 检索到的原始文档（可追溯）
    category=detected_category  # 自动检测的分类
)
```

### 3.3 完整流程图

```
用户: "怎么退货？"
    │
    ↓
┌─────────────────────────────────────────────────────┐
│  第一步: 检索 (Retrieval)                            │
│                                                      │
│  "怎么退货？"                                        │
│       ↓ BGE向量化                                    │
│  [0.78, 0.15, 0.92, ...]  ← 512维向量               │
│       ↓ ChromaDB HNSW 搜索                           │
│  找到最相似的3条文档:                                 │
│    1. "怎么退货？→ 7天内可申请..." (相似度: 0.95)     │
│    2. "退款多久到账？→ 3-5天..." (相似度: 0.72)      │
│    3. "可以换货吗？→ 联系客服..." (相似度: 0.65)     │
└─────────────────────────────────────────────────────┘
    │
    ↓
┌─────────────────────────────────────────────────────┐
│  第二步: 增强 (Augmented)                            │
│                                                      │
│  把检索到的3条文档 + 用户问题 组装成Prompt:           │
│  "你是电商客服。参考资料：[文档1][文档2][文档3]       │
│   用户问题：怎么退货？ 请回答。"                      │
└─────────────────────────────────────────────────────┘
    │
    ↓
┌─────────────────────────────────────────────────────┐
│  第三步: 生成 (Generation)                           │
│                                                      │
│  DeepSeek V4 Pro 读取Prompt，生成自然语言回答:       │
│  "亲，收到商品后7天内可以申请退货哦~                  │
│   退款将在3-5个工作日内原路返回。"                    │
└─────────────────────────────────────────────────────┘
    │
    ↓
返回给用户: {answer, sources, category}
```

### 3.4 为什么要分三步？每步的作用是什么？

| 步骤 | 作用 | 如果没有这步会怎样 |
|------|------|-------------------|
| **检索** | 从知识库找到真实信息 | LLM 会编造错误答案（幻觉） |
| **增强** | 把真实信息组装成 Prompt | LLM 不知道该参考什么 |
| **生成** | 把原始信息变成自然语言 | 用户看到的是生硬的 Q&A 对，不友好 |

**一句话总结**：**检索保证准确性，增强提供上下文，生成提升用户体验。**

---

## 四、三个技术的关系

```
向量化 (Embedder)          向量数据库 (VectorStore)        RAG
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ 把文字变数字  │ ──存入──→│ 存储和检索向量 │ ──检索──→│ 检索+增强+生成│
│ BGE模型      │          │ ChromaDB     │          │ 完整问答流程  │
└──────────────┘          └──────────────┘          └──────────────┘
     工具层                    存储层                    应用层
```

- **向量化**是工具：把文字翻译成数字
- **向量数据库**是仓库：存储数字，快速找到最相似的
- **RAG**是应用：用向量化和向量数据库实现智能问答

三者缺一不可。没有向量化，计算机无法理解文字；没有向量数据库，无法快速检索；没有 RAG，大模型会编造答案。

---

## 五、双知识库架构（qa_knowledge + doc_knowledge）

### 5.1 两个知识库的区别

| | 核心知识库 (qa_knowledge) | 文档知识库 (doc_knowledge) |
|---|---|---|
| **数据来源** | 淘宝客服对话数据集（8000条） | 用户自己上传的文件 |
| **数据结构** | 结构化 Q&A 对（问题+答案分离） | 原始文本块（500字切一刀） |
| **分类** | 有（9大类：物流、退换货、支付...） | 固定标记为"文档上传" |
| **质量** | 经过清洗、过滤正样本、人工标注 | 未处理，质量参差不齐 |
| **向量化输入** | 最近3轮对话 + 问题（带上下文） | 纯文本块（无上下文） |
| **metadata** | question, answer, category, source | source, chunk_index, upload_time |

### 5.2 类比理解

**核心知识库** = 教科书
- 内容经过专家审核
- 结构清晰（有章节、有答案）
- 可靠、准确

**文档知识库** = 随手扔进来的笔记
- 内容未经审核
- 结构混乱（就是一堆文字切成了块）
- 可能有用，也可能不准确

### 5.3 分层检索逻辑

代码位置：`api.py` 第 267-314 行

```python
# 第一步：优先从核心知识库检索
qa_results = qa_collection.query(...)

# 第二步：如果核心知识库结果不足，从文档知识库补充
if len(sources) < request.top_k:
    doc_results = doc_collection.query(...)
```

**设计思路**：

```
用户提问
    ↓
先查 qa_knowledge（可靠）
    ↓
找到 enough? → 是 → 直接用
    ↓ 否
再查 doc_knowledge（补充）
    ↓
合并结果，按相似度排序
```

**好处**：

1. **保证质量**：核心知识库的答案优先级更高
2. **覆盖面广**：核心知识库没有的，文档知识库可能有
3. **可管理**：清空上传文档不影响核心知识库

**一句话**：核心知识库是"标准答案库"，文档知识库是"扩展资料库"。先查标准答案，查不到再去翻资料。

