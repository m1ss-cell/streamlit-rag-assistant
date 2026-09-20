"""Chroma 向量库：embedding、持久化、检索器（可接入 LangChain chain）。"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from config_data import (
    COLLECTION_NAME,
    DASHSCOPE_API_KEY,
    DASHSCOPE_API_KEY_ENV,
    EMBEDDING_MODEL,
    RETRIEVER_SCORE_THRESHOLD,
    RETRIEVER_SEARCH_TYPE,
    RETRIEVER_TOP_K,
    VECTOR_DIR,
)


def ensure_vector_dir() -> Path:
    """确保本地向量库目录存在。"""
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    return VECTOR_DIR


@lru_cache(maxsize=1)
def get_embeddings() -> DashScopeEmbeddings:
    """
    创建 DashScopeEmbeddings。

    API Key 读取顺序：
    1. config_data.DASHSCOPE_API_KEY
    2. 环境变量（名称见 DASHSCOPE_API_KEY_ENV）
    """
    api_key = DASHSCOPE_API_KEY or os.getenv(DASHSCOPE_API_KEY_ENV)
    if not api_key:
        raise ValueError(
            f"未检测到 DashScope API Key，请在 config_data.py 填写 "
            f"DASHSCOPE_API_KEY，或设置环境变量 {DASHSCOPE_API_KEY_ENV}。"
        )
    return DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        dashscope_api_key=api_key,
    )


def get_vector_store() -> Chroma:
    """创建 / 加载本地持久化的 Chroma 向量库。"""
    persist_directory = str(ensure_vector_dir())
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=persist_directory,
    )


def add_documents_to_vector_store(documents: list[Document]) -> list[str]:
    """将切分后的文档转为 embedding，并保存到本地 Chroma 向量库。"""
    if not documents:
        return []
    vector_store = get_vector_store()
    ids = vector_store.add_documents(documents)
    # 旧版 langchain_community.Chroma 需要显式 persist
    if hasattr(vector_store, "persist"):
        vector_store.persist()
    return ids


def search_with_scores(
    query: str,
    k: int | None = None,
) -> list[tuple[Document, float]]:
    """
    检索文档并返回 (Document, relevance_score)。

    relevance_score 越大表示越相关（约 0~1）。
    """
    top_k = RETRIEVER_TOP_K if k is None else k
    vector_store = get_vector_store()
    return vector_store.similarity_search_with_relevance_scores(query, k=top_k)


def filter_by_score_threshold(
    results: list[tuple[Document, float]],
    score_threshold: float | None = None,
) -> list[Document]:
    """按相关度阈值过滤；低于阈值的文档丢弃。"""
    threshold = (
        RETRIEVER_SCORE_THRESHOLD if score_threshold is None else score_threshold
    )
    return [doc for doc, score in results if score >= threshold]


def search_relevant_documents(
    query: str,
    k: int | None = None,
    score_threshold: float | None = None,
) -> list[Document]:
    """
    只返回“足够相关”的文档。

    若全部低于阈值，返回空列表（表示知识库中无相关资料）。
    """
    scored = search_with_scores(query, k=k)
    return filter_by_score_threshold(scored, score_threshold=score_threshold)


def get_retriever(
    k: int | None = None,
    search_type: str | None = None,
    score_threshold: float | None = None,
) -> BaseRetriever:
    """
    返回可接入 LangChain chain 的向量检索器。

    默认使用 similarity_score_threshold：
    仅返回相关度 >= RETRIEVER_SCORE_THRESHOLD 的文档；
    若都不相关，则返回空列表，避免把无关资料塞给大模型。

    Args:
        k: 返回文档数量上限，默认 config_data.RETRIEVER_TOP_K
        search_type: similarity / similarity_score_threshold / mmr
        score_threshold: 相关度阈值（仅 score_threshold 模式生效）
    """
    top_k = RETRIEVER_TOP_K if k is None else k
    stype = RETRIEVER_SEARCH_TYPE if search_type is None else search_type
    threshold = (
        RETRIEVER_SCORE_THRESHOLD if score_threshold is None else score_threshold
    )

    search_kwargs: dict = {"k": top_k}
    if stype == "similarity_score_threshold":
        search_kwargs["score_threshold"] = threshold

    vector_store = get_vector_store()
    return vector_store.as_retriever(
        search_type=stype,
        search_kwargs=search_kwargs,
    )


if __name__ == "__main__":
    query = "今天北京天气怎么样"
    print("查询:", query)
    scored = search_with_scores(query)
    print("原始检索（含分数）:")
    for doc, score in scored:
        print(f"  score={score:.4f} | {doc.page_content[:40]!r}...")

    filtered = filter_by_score_threshold(scored)
    print(f"阈值 {RETRIEVER_SCORE_THRESHOLD} 过滤后数量:", len(filtered))

    retriever = get_retriever()
    print("retriever 结果:", retriever.invoke(query))
