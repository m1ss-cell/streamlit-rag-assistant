# Streamlit RAG Assistant

基于 **Streamlit + LangChain + Chroma + 通义千问（DashScope）** 的本地 RAG 智能客服系统。

支持：上传 TXT 知识文档 → 去重入库 → 向量检索 → 大模型流式问答，并带有多轮会话历史。

---

## 功能概览

| 模块       | 说明                                                 |
| ---------- | ---------------------------------------------------- |
| 知识上传页 | 多选 TXT，串行写入知识库；内容去重；分段 + Embedding |
| 智能客服页 | ChatGPT 风格对话；流式回答；左右气泡布局             |
| 向量检索   | Chroma 本地持久化；相关度阈值过滤无关文档            |
| 会话历史   | 按用户 ID 保存到本地 JSON，并注入 Prompt             |
| 页面切换   | 左侧边栏可在「智能客服 / 上传知识」间切换            |

---

## 项目结构

```text
.
├── app.py                  # 推荐启动入口（统一导航）
├── app_qa.py               # 智能客服问答页
├── app_file_uploader.py    # 知识文档上传页
├── page_nav.py             # 页面切换导航
├── config_data.py          # 全局配置（模型、路径、阈值等）
├── knowledge_base.py       # store 去重 + 入库编排
├── vector_stores.py        # Chroma 向量库 / 检索器
├── rag.py                  # RAG chain（检索 + 历史 + 流式生成）
├── file_history_store.py   # 本地会话历史
├── data/                   # 示例 TXT 知识文档（可选用）
├── store/                  # 上传原文与元信息（运行后生成）
├── vector_store/           # Chroma 持久化目录（运行后生成）
└── chat_history/           # 用户对话历史（运行后生成）
```

---

## 环境要求

- Python 3.10+（建议 3.10 / 3.11）
- 可访问阿里云 DashScope（通义千问）API
- DashScope API Key（用于 Embedding + Chat）

---

## 快速开始

### 1. 克隆项目

```bash
git clone <你的仓库地址>
cd <项目目录>
```

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 API Key

任选一种方式：

**方式 A：环境变量（推荐）**

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY="sk-xxxxxxxx"

# macOS / Linux
export DASHSCOPE_API_KEY="sk-xxxxxxxx"
```

**方式 B：写在配置文件**

编辑 `config_data.py`：

```python
DASHSCOPE_API_KEY = "sk-xxxxxxxx"
```

> 注意：不要把真实 Key 提交到 GitHub。

### 5. 启动网页

```bash
streamlit run app.py
```

浏览器打开后：

1. 左侧切换到 **上传知识**
2. 选择一个或多个 `.txt` 文件，点击 **开始上传到知识库**
3. 再切回 **智能客服**，开始提问

示例问题：

- `深色衣服怎么洗？`
- `黄皮适合穿什么颜色？`
- `身高 175 体重 70 穿什么尺码？`

---

## 使用说明

### 上传知识

1. 可一次多选，或分多次添加（先临时记录）
2. 点击「开始上传到知识库」后串行处理，并显示进度
3. 相同内容（按 SHA256）不会重复入库
4. 成功后会写入：
   - `store/knowledge_store.txt`（原文 + 元信息）
   - `vector_store/`（向量索引）

### 智能客服

1. 输入问题后，系统会：
   - 读取该用户历史会话
   - 从向量库检索相关资料（低于相关度阈值则视为无资料）
   - 调用 `qwen3-max` 流式生成回答
2. 默认用户 ID：`User_001`（见 `config_data.py`）
3. 「清空对话」会清空页面消息与本地历史文件

---

## 常用配置（`config_data.py`）

| 配置项                         | 含义                     | 默认                |
| ------------------------------ | ------------------------ | ------------------- |
| `CHAT_MODEL`                   | 对话模型                 | `qwen3-max`         |
| `EMBEDDING_MODEL`              | 向量模型                 | `text-embedding-v4` |
| `RETRIEVER_TOP_K`              | 最多检索条数             | `3`                 |
| `RETRIEVER_SCORE_THRESHOLD`    | 相关度阈值（越大越严格） | `0.3`               |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 文本分段参数             | `500` / `50`        |
| `DEFAULT_USER_ID`              | 默认用户                 | `User_001`          |
| `HISTORY_MAX_TURNS`            | 注入 Prompt 的最近轮数   | `6`                 |

如果回答经常带上无关资料：把 `RETRIEVER_SCORE_THRESHOLD` 调高（如 `0.45`）。  
如果相关资料经常被过滤掉：把阈值调低（如 `0.2`）。

---

## 命令行自测（可选）

```bash
# 测试向量检索
python vector_stores.py

# 测试 RAG 流式问答（会打印最终提示词）
python rag.py
```

---

## 技术链路

```text
TXT 上传
  → store 去重（SHA256）
  → 文本分段（RecursiveCharacterTextSplitter）
  → DashScope Embedding（text-embedding-v4）
  → Chroma 本地向量库

用户提问
  → 注入历史会话
  → 向量检索（带相关度阈值）
  → Prompt + ChatTongyi(qwen3-max)
  → 流式输出到网页
```

---

## 注意事项

1. 首次上传与首次问答需要可访问 DashScope 网络。
2. `store/`、`vector_store/`、`chat_history/` 为运行时数据，可不提交仓库。
3. 当前仅支持 `.txt` 知识文件。
4. 暂未接入真实用户数据库，用户 ID 固定为配置中的默认值。

---

## License

本项目用于学习与演示，可按需自行补充 License。
