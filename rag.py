"""RAG 问答：检索本地向量库 + 历史会话注入 + ChatTongyi 流式 chain。"""

from __future__ import annotations

import os
from collections.abc import Iterator
from functools import lru_cache

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from config_data import (
    CHAT_MODEL,
    CHAT_STREAMING,
    CHAT_TEMPERATURE,
    CHAT_TOP_P,
    DASHSCOPE_API_KEY,
    DASHSCOPE_API_KEY_ENV,
    DEFAULT_USER_ID,
    RAG_SYSTEM_PROMPT,
)
from file_history_store import append_turn, format_history_for_prompt
from vector_stores import get_retriever


def _resolve_api_key() -> str:
    api_key = DASHSCOPE_API_KEY or os.getenv(DASHSCOPE_API_KEY_ENV)
    if not api_key:
        raise ValueError(
            f"未检测到 DashScope API Key，请在 config_data.py 填写 "
            f"DASHSCOPE_API_KEY，或设置环境变量 {DASHSCOPE_API_KEY_ENV}。"
        )
    return api_key


@lru_cache(maxsize=1)
def get_chat_model() -> ChatTongyi:
    """创建聊天模型（默认 qwen3-max，参数见 config_data）。"""
    return ChatTongyi(
        model=CHAT_MODEL,
        dashscope_api_key=_resolve_api_key(),
        temperature=CHAT_TEMPERATURE,
        top_p=CHAT_TOP_P,
        streaming=CHAT_STREAMING,
    )


def get_prompt_template() -> ChatPromptTemplate:
    """
    构建 RAG 提示词模板。

    注入：历史会话 + 参考资料 + 用户问题
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                RAG_SYSTEM_PROMPT
                + "回答时可结合历史会话理解指代，但事实依据仍以参考资料为主。",
            ),
            (
                "human",
                "【历史会话】\n{history}\n\n"
                "【参考资料】\n{context}\n\n"
                "【用户问题】\n{question}",
            ),
        ]
    )


def format_docs(docs: list[Document]) -> str:
    """将检索到的 Document 列表格式化为上下文文本。"""
    if not docs:
        return (
            "（未检索到与问题相关的参考资料。"
            "请明确告知用户：本地知识库中没有相关信息。）"
        )
    parts = []
    for index, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[资料{index} | 来源: {source}]\n{doc.page_content}")
    return "\n\n".join(parts)


def build_rag_inputs(
    question: str,
    user_id: str | None = None,
) -> dict[str, str]:
    """
    组装 chain 输入：历史会话 + 向量检索资料 + 当前问题。
    """
    uid = user_id or DEFAULT_USER_ID
    question = (question or "").strip()
    retriever = get_retriever()
    docs = retriever.invoke(question)
    return {
        "history": format_history_for_prompt(uid),
        "context": format_docs(docs),
        "question": question,
    }


def build_final_prompt(
    question: str,
    user_id: str | None = None,
) -> ChatPromptValue:
    """检索知识库、读取历史并填充模板，返回最终提示词。"""
    inputs = build_rag_inputs(question, user_id=user_id)
    return get_prompt_template().invoke(inputs)


def format_prompt_for_print(prompt_value: ChatPromptValue) -> str:
    """将最终提示词格式化为可读文本。"""
    lines: list[str] = []
    messages: list[BaseMessage] = prompt_value.to_messages()
    for message in messages:
        role = message.type.upper()
        lines.append(f"----- {role} -----")
        lines.append(
            message.content if isinstance(message.content, str) else str(message.content)
        )
        lines.append("")
    return "\n".join(lines).rstrip()


@lru_cache(maxsize=1)
def get_rag_chain() -> Runnable:
    """
    构建回答 chain（支持 stream）：

    输入 dict{history, context, question}
      → prompt
      → chat_model
      → 字符串片段
    """
    return get_prompt_template() | get_chat_model() | StrOutputParser()


def ask_stream(
    question: str,
    user_id: str | None = None,
    *,
    save_history: bool = True,
) -> Iterator[str]:
    """
    流式执行 RAG 问答。

    - 按 user_id 读取历史并注入 prompt
    - 回答结束后将本轮对话写入本地历史文件
    """
    uid = user_id or DEFAULT_USER_ID
    question = (question or "").strip()
    if not question:
        yield "请输入有效的问题。"
        return

    inputs = build_rag_inputs(question, user_id=uid)
    chain = get_rag_chain()
    answer_parts: list[str] = []
    for chunk in chain.stream(inputs):
        if chunk:
            answer_parts.append(chunk)
            yield chunk

    if save_history and answer_parts:
        append_turn(question, "".join(answer_parts), user_id=uid)


def ask(
    question: str,
    user_id: str | None = None,
    *,
    save_history: bool = True,
) -> str:
    """非流式便捷接口：内部走 stream，最终拼接完整回答。"""
    return "".join(
        ask_stream(question, user_id=user_id, save_history=save_history)
    )


# 模块级便捷对象，便于外部直接引用
chat_model = None
prompt_template = None
chain = None


def init_rag() -> Runnable:
    """初始化并缓存 chat_model / prompt_template / chain。"""
    global chat_model, prompt_template, chain
    get_chat_model.cache_clear()
    get_rag_chain.cache_clear()
    chat_model = get_chat_model()
    prompt_template = get_prompt_template()
    chain = get_rag_chain()
    return chain


if __name__ == "__main__":
    init_rag()
    demo_user = DEFAULT_USER_ID
    demo_question = "什么材质的衣服最舒服？"
    print("用户:", demo_user)
    print("问题:", demo_question)
    print()

    final_prompt = build_final_prompt(demo_question, user_id=demo_user)
    print("========== 最终提示词 ==========")
    print(format_prompt_for_print(final_prompt))
    print("================================")
    print()

    print("回答（流式）:")
    for piece in ask_stream(demo_question, user_id=demo_user):
        print(piece, end="", flush=True)
    print()
