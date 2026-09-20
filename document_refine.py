"""上传文档大模型整理：总结并结构化后写入知识库。"""

from __future__ import annotations

import os
from functools import lru_cache

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config_data import (
    CHAT_MODEL,
    CHAT_TEMPERATURE,
    CHAT_TOP_P,
    DASHSCOPE_API_KEY,
    DASHSCOPE_API_KEY_ENV,
    DOC_REFINE_MAX_CHARS,
    DOC_REFINE_SYSTEM_PROMPT,
)


def _resolve_api_key() -> str:
    api_key = DASHSCOPE_API_KEY or os.getenv(DASHSCOPE_API_KEY_ENV)
    if not api_key:
        raise ValueError(
            f"未检测到 DashScope API Key，请在 config_data.py 填写 "
            f"DASHSCOPE_API_KEY，或设置环境变量 {DASHSCOPE_API_KEY_ENV}。"
        )
    return api_key


@lru_cache(maxsize=1)
def get_refine_model() -> ChatTongyi:
    """文档整理模型（关闭流式，便于一次拿到完整整理结果）。"""
    return ChatTongyi(
        model=CHAT_MODEL,
        dashscope_api_key=_resolve_api_key(),
        temperature=CHAT_TEMPERATURE,
        top_p=CHAT_TOP_P,
        streaming=False,
    )


def get_refine_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", DOC_REFINE_SYSTEM_PROMPT),
            (
                "human",
                "文件名：{filename}\n\n原始内容：\n{content}",
            ),
        ]
    )


def refine_document_text(raw_text: str, filename: str | None = None) -> str:
    """
    调用大模型对原始文档进行总结与结构化整理。

    Returns:
        整理后的知识库正文
    """
    content = (raw_text or "").strip()
    if not content:
        raise ValueError("原始文档内容为空，无法整理")

    truncated = False
    if len(content) > DOC_REFINE_MAX_CHARS:
        content = content[:DOC_REFINE_MAX_CHARS]
        truncated = True

    if truncated:
        content += "\n\n（注：原文过长，仅整理截断后的前半部分内容。）"

    chain = get_refine_prompt() | get_refine_model() | StrOutputParser()
    result = chain.invoke(
        {
            "filename": filename or "unknown",
            "content": content,
        }
    )
    refined = (result or "").strip()
    if not refined:
        raise ValueError("大模型未返回有效的整理结果")
    return refined
