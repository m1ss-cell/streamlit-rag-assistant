"""页面导航：智能客服 ↔ 知识上传（固定在左侧，不随聊天滚动）。"""

from __future__ import annotations

import streamlit as st


def ensure_page_state(default: str = "qa") -> None:
    if "current_page" not in st.session_state:
        st.session_state.current_page = default


def go_to(page: str) -> None:
    """切换到指定页面：qa / upload。"""
    st.session_state.current_page = page
    st.rerun()


def render_nav(active: str) -> None:
    """左侧边栏导航：不随主内容滚动，始终可点击。"""
    ensure_page_state()

    with st.sidebar:
        st.markdown("### 页面切换")
        st.caption("可随时在问答与上传间切换")

        qa_clicked = st.button(
            "💬 智能客服",
            use_container_width=True,
            type="primary" if active == "qa" else "secondary",
            key=f"nav_qa_{active}",
        )
        upload_clicked = st.button(
            "📄 上传知识",
            use_container_width=True,
            type="primary" if active == "upload" else "secondary",
            key=f"nav_upload_{active}",
        )

        st.divider()
        st.caption("当前：" + ("智能客服" if active == "qa" else "上传知识"))

    if qa_clicked and active != "qa":
        go_to("qa")
    if upload_clicked and active != "upload":
        go_to("upload")
