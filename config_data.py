"""项目配置：路径、模型、文本分割等集中管理，便于统一修改。"""

from __future__ import annotations

from pathlib import Path

# =========================
# 项目根目录
# =========================
BASE_DIR = Path(__file__).resolve().parent

# =========================
# Store 文本库（内容去重）
# =========================
STORE_DIR = BASE_DIR / "store"
STORE_FILE = STORE_DIR / "knowledge_store.txt"
DOC_SEPARATOR = "\n\n===== DOC_SEPARATOR =====\n\n"
DEFAULT_UPLOADER = "User"  # 暂未接入数据库，默认上传者
UPLOAD_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# =========================
# Chroma 向量库
# =========================
VECTOR_DIR = BASE_DIR / "vector_store"
COLLECTION_NAME = "knowledge_base"
# 向量检索器返回的文档数量（可用于 RAG chain）
RETRIEVER_TOP_K = 3
# 检索类型：
# - similarity：始终返回 top_k（可能不相关）
# - similarity_score_threshold：只返回相关度 >= 阈值的文档
# - mmr：最大边际相关性
RETRIEVER_SEARCH_TYPE = "similarity_score_threshold"
# 相关度阈值（0~1，越大越严格）；低于该值视为“无相关资料”，不送入大模型
RETRIEVER_SCORE_THRESHOLD = 0.3

# =========================
# Chat 模型（通义千问 / DashScope）
# =========================
CHAT_MODEL = "qwen3-max"
CHAT_TEMPERATURE = 0.2
CHAT_TOP_P = 0.8
CHAT_STREAMING = True

# =========================
# RAG 提示词
# =========================
RAG_SYSTEM_PROMPT = (
    "你是一个专业的知识库问答助手。"
    "请以本地知识库参考资料为主，简洁、专业地回答用户问题。"
    "若参考资料为空、标注为未检索到相关资料，或资料与问题明显无关，"
    "请直接说明知识库中没有相关信息，不要编造答案。"
)

# =========================
# Embedding 模型（DashScope）
# =========================
EMBEDDING_MODEL = "text-embedding-v4"
# 优先读环境变量；也可在此直接填写（不推荐把真实 key 提交到仓库）
DASHSCOPE_API_KEY_ENV = "DASHSCOPE_API_KEY"
DASHSCOPE_API_KEY = ""  # 例如: "sk-xxx"；为空则使用环境变量

# =========================
# 文本分割（RecursiveCharacterTextSplitter）
# =========================
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TEXT_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", " ", ""]

# =========================
# 历史会话（本地文件）
# =========================
HISTORY_DIR = BASE_DIR / "chat_history"
DEFAULT_USER_ID = "User_001"  # 暂未接入数据库，默认用户
# 注入 prompt 时最多使用最近多少轮对话（一轮 = 用户问 + 助手答）
HISTORY_MAX_TURNS = 6

# =========================
# 文档整理（上传后交给大模型总结）
# =========================
DOC_REFINE_MAX_CHARS = 12000  # 送入整理模型的原文最大字符数
DOC_REFINE_SYSTEM_PROMPT = (
    "你是知识库文档整理助手。"
    "请阅读用户上传的原始文档内容，进行总结与结构化整理，"
    "输出适合写入 RAG 知识库的中文文本。"
    "要求：\n"
    "1. 保留关键事实、规则、步骤与要点，删除无关废话与重复内容；\n"
    "2. 结构清晰，可用小标题与分点；\n"
    "3. 不要编造原文不存在的信息；\n"
    "4. 只输出整理后的正文，不要额外解释。"
)

# =========================
# 网页上传相关
# =========================
# Streamlit file_uploader 支持的扩展名（不含点）
ALLOWED_UPLOAD_EXTENSIONS = [
    "txt",
    "md",
    "markdown",
    "csv",
    "json",
    "html",
    "htm",
    "pdf",
    "docx",
    "doc",
    "xlsx",
    "xls",
    "pptx",
    "ppt",
    "log",
]
PREVIEW_CHARS = 300
