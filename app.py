"""统一入口：智能客服 / 知识上传 页面切换。"""

from __future__ import annotations

import streamlit as st

from page_nav import ensure_page_state

st.set_page_config(
    page_title="RAG 智能客服系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_page_state()

if st.session_state.current_page == "upload":
    from app_file_uploader import render_upload_page

    render_upload_page()
else:
    from app_qa import render_qa_page

    render_qa_page()
