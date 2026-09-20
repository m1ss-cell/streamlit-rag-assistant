"""智能客服聊天页：Streamlit + 本地知识库 RAG 流式问答。"""

from __future__ import annotations

import html

import streamlit as st

from config_data import CHAT_MODEL, DEFAULT_USER_ID
from file_history_store import clear_history, load_history
from page_nav import render_nav
from rag import ask_stream, init_rag


def _inject_styles() -> None:
    st.markdown(
        """
    <style>
    .stApp {
        background:
            radial-gradient(900px 420px at 0% -10%, #e2e8f0 0%, transparent 55%),
            radial-gradient(800px 380px at 100% 0%, #dbeafe 0%, transparent 50%),
            #f8fafc;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 6.5rem;
        max-width: 820px;
    }

    .chat-hero {
        text-align: center;
        margin: 0.4rem 0 1.2rem 0;
    }

    .chat-hero h1 {
        margin: 0;
        font-size: 1.7rem;
        font-weight: 750;
        color: #0f172a;
        letter-spacing: -0.03em;
    }

    .chat-hero p {
        margin: 0.4rem 0 0 0;
        color: #64748b;
        font-size: 0.92rem;
    }

    .meta-bar {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-bottom: 1rem;
    }

    .meta-chip {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        color: #475569;
        border-radius: 999px;
        padding: 0.25rem 0.7rem;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .welcome-card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.4rem 1.3rem;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.04);
        margin: 1.5rem 0 0.5rem 0;
    }

    .welcome-card h3 {
        margin: 0 0 0.55rem 0;
        color: #0f172a;
        font-size: 1.05rem;
    }

    .welcome-card ul {
        margin: 0;
        padding-left: 1.1rem;
        color: #64748b;
        font-size: 0.9rem;
        line-height: 1.7;
    }

    .msg-row {
        display: flex;
        width: 100%;
        margin: 0.65rem 0;
    }

    .msg-row.user {
        justify-content: flex-end;
    }

    .msg-row.ai {
        justify-content: flex-start;
    }

    .bubble {
        max-width: 78%;
        padding: 0.7rem 0.9rem;
        border-radius: 16px;
        font-size: 0.95rem;
        line-height: 1.45;
        word-break: break-word;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }

    .bubble-content {
        margin: 0;
        padding: 0;
        line-height: 1.45;
    }

    .bubble-content br {
        content: "";
        display: block;
        margin: 0.12rem 0;
    }

    .bubble.user {
        background: #2563eb;
        color: #ffffff;
        border-bottom-right-radius: 6px;
    }

    .bubble.ai {
        background: #ffffff;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        border-bottom-left-radius: 6px;
    }

    .bubble-label {
        font-size: 0.72rem;
        font-weight: 650;
        margin-bottom: 0.28rem;
        opacity: 0.85;
    }

    .bubble.user .bubble-label {
        color: #dbeafe;
        text-align: right;
    }

    .bubble.ai .bubble-label {
        color: #64748b;
        text-align: left;
    }

    div[data-testid="stChatInput"] textarea {
        border-radius: 14px !important;
    }

    div[data-testid="stButton"] > button {
        border-radius: 10px;
        font-weight: 600;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def history_to_messages(user_id: str) -> list[dict]:
    """把本地历史转为页面消息列表。"""
    messages: list[dict] = []
    for item in load_history(user_id):
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            messages.append({"role": "user", "content": content})
        elif role == "assistant":
            messages.append({"role": "assistant", "content": content})
    return messages


def normalize_bubble_text(content: str) -> str:
    """压缩多余空行，避免气泡里行距显得过大。"""
    text = (content or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    # 连续空行最多保留 1 个换行效果（显示时再转 br）
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    # 把“空行”再压成单换行，减少视觉空隙
    text = text.replace("\n\n", "\n")
    return text


def render_bubble(role: str, content: str, *, cursor: bool = False) -> str:
    """生成左右对齐、异色气泡 HTML。"""
    text = normalize_bubble_text(content)
    safe = html.escape(text).replace("\n", "<br>")
    if cursor:
        safe = f"{safe}<span style='opacity:0.55'>▌</span>"

    if role == "user":
        return (
            '<div class="msg-row user">'
            '<div class="bubble user">'
            '<div class="bubble-label">你</div>'
            f'<div class="bubble-content">{safe}</div>'
            "</div></div>"
        )

    return (
        '<div class="msg-row ai">'
        '<div class="bubble ai">'
        '<div class="bubble-label">智能客服</div>'
        f'<div class="bubble-content">{safe}</div>'
        "</div></div>"
    )


def init_page_state() -> None:
    if "qa_ready" not in st.session_state:
        try:
            init_rag()
            st.session_state.qa_ready = True
            st.session_state.qa_error = None
        except Exception as exc:  # noqa: BLE001
            st.session_state.qa_ready = False
            st.session_state.qa_error = str(exc)

    if "user_id" not in st.session_state:
        st.session_state.user_id = DEFAULT_USER_ID

    if "messages" not in st.session_state:
        st.session_state.messages = history_to_messages(st.session_state.user_id)


def render_header() -> None:
    st.markdown(
        f"""
        <div class="chat-hero">
            <h1>智能客服</h1>
            <p>基于本地知识库检索，结合大模型为你专业作答</p>
        </div>
        <div class="meta-bar">
            <span class="meta-chip">用户 {st.session_state.user_id}</span>
            <span class="meta-chip">模型 {CHAT_MODEL}</span>
            <span class="meta-chip">RAG 知识库</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_welcome() -> None:
    st.markdown(
        """
        <div class="welcome-card">
            <h3>你好，我是你的知识库助手</h3>
            <ul>
                <li>可以直接问尺码、洗涤、颜色搭配等问题</li>
                <li>我会优先参考本地知识库中的资料</li>
                <li>支持多轮对话，会记住本次会话上下文</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def clear_conversation() -> None:
    clear_history(st.session_state.user_id)
    st.session_state.messages = []


def render_qa_page() -> None:
    """渲染智能客服问答页（可由 app.py 调用）。"""
    _inject_styles()
    init_page_state()
    render_nav("qa")
    render_header()

    top_cols = st.columns([1, 1, 1])
    with top_cols[1]:
        if st.button("清空对话", use_container_width=True, key="qa_clear_chat"):
            clear_conversation()
            st.rerun()

    if not st.session_state.qa_ready:
        st.error(
            "智能客服初始化失败，请检查 API Key 与依赖配置。\n\n"
            f"详情：{st.session_state.qa_error}"
        )
        st.stop()

    if not st.session_state.messages:
        render_welcome()
    else:
        for message in st.session_state.messages:
            st.markdown(
                render_bubble(message["role"], message["content"]),
                unsafe_allow_html=True,
            )

    user_input = st.chat_input("输入你的问题，例如：深色衣服怎么洗？")

    if user_input:
        question = user_input.strip()
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            st.markdown(render_bubble("user", question), unsafe_allow_html=True)

            placeholder = st.empty()
            chunks: list[str] = []
            try:
                for piece in ask_stream(
                    question,
                    user_id=st.session_state.user_id,
                    save_history=True,
                ):
                    chunks.append(piece)
                    placeholder.markdown(
                        render_bubble("assistant", "".join(chunks), cursor=True),
                        unsafe_allow_html=True,
                    )
                answer = "".join(chunks).strip() or "（未生成有效回答）"
                placeholder.markdown(
                    render_bubble("assistant", answer),
                    unsafe_allow_html=True,
                )
            except Exception as exc:  # noqa: BLE001
                answer = f"回答失败：{exc}"
                placeholder.markdown(
                    render_bubble("assistant", answer),
                    unsafe_allow_html=True,
                )

            st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    from page_nav import ensure_page_state

    st.set_page_config(
        page_title="智能客服",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    ensure_page_state()
    if st.session_state.current_page == "upload":
        from app_file_uploader import render_upload_page

        render_upload_page()
    else:
        render_qa_page()
