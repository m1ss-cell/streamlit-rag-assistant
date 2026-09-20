"""本地知识库：store 文本去重 + 调用向量库完成入库。"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config_data import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DEFAULT_UPLOADER,
    DOC_SEPARATOR,
    STORE_DIR,
    STORE_FILE,
    TEXT_SEPARATORS,
    UPLOAD_TIME_FORMAT,
    VECTOR_DIR,
)
from vector_stores import add_documents_to_vector_store


def normalize_content(content: str) -> str:
    """统一换行与首尾空白，便于稳定比对。"""
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def content_hash(content: str) -> str:
    """对规范化后的内容计算 SHA256。"""
    return hashlib.sha256(normalize_content(content).encode("utf-8")).hexdigest()


def ensure_store() -> Path:
    """确保 store 目录与 store 文件存在，返回 store 文件路径。"""
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    if not STORE_FILE.exists():
        STORE_FILE.write_text("", encoding="utf-8")
    return STORE_FILE


def read_store() -> str:
    """读取本地 store 文件全文。"""
    store_path = ensure_store()
    return store_path.read_text(encoding="utf-8")


# store 元信息行格式：[key: value]
_META_LINE_RE = re.compile(r"^\[(?P<key>[^\]:]+):\s*(?P<value>.*)\]\s*$")


def extract_doc_body(doc_chunk: str) -> str:
    """从 store 中的一段内容提取正文（忽略开头的元信息行）。"""
    text = normalize_content(doc_chunk)
    lines = text.split("\n")
    body_start = 0
    for index, line in enumerate(lines):
        if _META_LINE_RE.match(line.strip()):
            body_start = index + 1
            continue
        break
    return normalize_content("\n".join(lines[body_start:]))


def build_store_chunk(
    content: str,
    filename: str | None = None,
    uploader: str | None = None,
) -> tuple[str, str, str, str]:
    """
    组装写入 store 的文本块。

    Returns:
        (chunk, sha256, uploader, upload_time)
    """
    normalized = normalize_content(content)
    file_hash = content_hash(normalized)
    upload_time = datetime.now().strftime(UPLOAD_TIME_FORMAT)
    uploader_name = uploader or DEFAULT_UPLOADER

    meta_lines = [
        f"[source: {filename or 'unknown'}]",
        f"[uploader: {uploader_name}]",
        f"[upload_time: {upload_time}]",
        f"[sha256: {file_hash}]",
    ]
    chunk = "\n".join(meta_lines) + "\n\n" + normalized
    return chunk, file_hash, uploader_name, upload_time


def split_store_docs(store_text: str) -> list[str]:
    """将 store 文件拆成多段已上传文档正文。"""
    if not store_text.strip():
        return []
    parts = store_text.split(DOC_SEPARATOR)
    bodies = [extract_doc_body(part) for part in parts]
    return [body for body in bodies if body]


def find_existing_in_store(content: str) -> bool:
    """根据内容（SHA256）判断是否已存在于本地 store 文件中。"""
    target = normalize_content(content)
    if not target:
        return False

    target_digest = content_hash(target)
    store_text = read_store()

    # 优先直接匹配已记录的 sha256 元信息
    if f"[sha256: {target_digest}]" in store_text:
        return True

    # 兼容旧格式（没有 sha256 元信息时，回退到正文比对）
    for doc_body in split_store_docs(store_text):
        if content_hash(doc_body) == target_digest:
            return True
    return False


def is_content_uploaded(content: str) -> bool:
    """判断内容是否已上传过（是否已在本地 store 文件中）。"""
    return find_existing_in_store(content)


def save_text_to_store(
    content: str,
    filename: str | None = None,
    uploader: str | None = None,
) -> dict:
    """
    将 TXT 内容保存到本地 store 文件中。

    额外记录：上传时间、上传者、SHA256。
    - 若内容已存在：跳过写入
    - 若内容不存在：追加到 store 文件末尾
    """
    store_path = ensure_store()
    normalized = normalize_content(content)
    file_hash = content_hash(normalized)
    uploader_name = uploader or DEFAULT_UPLOADER

    if not normalized:
        return {
            "success": False,
            "skipped": True,
            "message": "内容为空，未保存",
            "path": str(store_path),
            "content_hash": file_hash,
            "uploader": uploader_name,
            "upload_time": None,
        }

    if find_existing_in_store(normalized):
        return {
            "success": True,
            "skipped": True,
            "message": "内容已存在于 store 文件中，跳过保存",
            "path": str(store_path),
            "content_hash": file_hash,
            "uploader": uploader_name,
            "upload_time": None,
        }

    chunk, file_hash, uploader_name, upload_time = build_store_chunk(
        normalized,
        filename=filename,
        uploader=uploader_name,
    )

    existing = read_store().rstrip()
    if existing:
        new_text = existing + DOC_SEPARATOR + chunk + "\n"
    else:
        new_text = chunk + "\n"

    store_path.write_text(new_text, encoding="utf-8")

    return {
        "success": True,
        "skipped": False,
        "message": f"已追加保存到：{store_path.name}",
        "path": str(store_path),
        "content_hash": file_hash,
        "uploader": uploader_name,
        "upload_time": upload_time,
    }


def get_text_splitter(
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> RecursiveCharacterTextSplitter:
    """创建文本段落分割器。"""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=TEXT_SEPARATORS,
        length_function=len,
    )


def split_text(content: str, filename: str | None = None) -> list[Document]:
    """将长文本切分为若干 Document 段落。"""
    splitter = get_text_splitter()
    metadata = {
        "source": filename or "unknown",
        "doc_hash": content_hash(content),
    }
    return splitter.create_documents([normalize_content(content)], metadatas=[metadata])


def ingest_text_to_knowledge_base(
    content: str,
    filename: str | None = None,
    uploader: str | None = None,
) -> dict:
    """
    将传入字符串写入知识库（store 去重 + 向量化入库）。

    流程：
    1. 在 store 中按内容判断是否已存在
    2. 已存在 → 跳过，不写入向量库
    3. 不存在 → 文本分割 → embedding → 保存到本地向量库，并同步写入 store
    """
    normalized = normalize_content(content)
    file_hash = content_hash(normalized)

    if not normalized:
        return {
            "success": False,
            "skipped": True,
            "message": "内容为空，未处理",
            "content_hash": file_hash,
            "chunk_count": 0,
            "store_path": str(STORE_FILE),
            "vector_dir": str(VECTOR_DIR),
        }

    if is_content_uploaded(normalized):
        return {
            "success": True,
            "skipped": True,
            "message": "内容已存在于 store 中，跳过向量化",
            "content_hash": file_hash,
            "chunk_count": 0,
            "store_path": str(STORE_FILE),
            "vector_dir": str(VECTOR_DIR),
        }

    # 1) 段落分割
    documents = split_text(normalized, filename=filename)

    # 2) embedding + 写入本地 Chroma（由 vector_stores 负责）
    ids = add_documents_to_vector_store(documents)

    # 3) 同步写入 store，供下次去重
    store_result = save_text_to_store(
        normalized,
        filename=filename,
        uploader=uploader,
    )

    return {
        "success": True,
        "skipped": False,
        "message": f"已分割为 {len(documents)} 段并写入向量库",
        "content_hash": file_hash,
        "chunk_count": len(documents),
        "vector_ids": ids,
        "store_path": store_result.get("path"),
        "vector_dir": str(VECTOR_DIR),
        "uploader": store_result.get("uploader"),
        "upload_time": store_result.get("upload_time"),
    }


def save_uploaded_texts(files: list[dict]) -> list[dict]:
    """
    批量将网页上传的多个文件写入知识库。

    files 每项建议包含：
        - name: 文件名（可选）
        - content: 文件内容
        - uploader: 上传者（可选）
    """
    results = []
    for item in files:
        name = item.get("name")
        content = item.get("content") or ""
        uploader = item.get("uploader")
        result = ingest_text_to_knowledge_base(
            content,
            filename=name,
            uploader=uploader,
        )
        result["name"] = name
        results.append(result)
    return results


if __name__ == "__main__":
    demo = "这是一段用于测试向量入库的文本。服装尺码选择需要结合身高、体重和版型。"
    print("第一次入库:", ingest_text_to_knowledge_base(demo, "demo.txt"))
    print("第二次入库:", ingest_text_to_knowledge_base(demo, "demo_again.txt"))
    print("store 路径:", STORE_FILE)
    print("向量库目录:", VECTOR_DIR)
