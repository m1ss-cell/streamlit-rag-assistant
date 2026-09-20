import html

import streamlit as st

from config_data import ALLOWED_UPLOAD_EXTENSIONS, DEFAULT_UPLOADER, PREVIEW_CHARS
from document_loader import extract_text_from_upload
from knowledge_base import ingest_uploaded_document
from page_nav import render_nav


def _inject_upload_styles() -> None:
    st.markdown(
        """
    <style>
    .stApp {
        background:
            radial-gradient(1200px 500px at 10% -10%, #dbeafe 0%, transparent 55%),
            radial-gradient(900px 400px at 100% 0%, #e2e8f0 0%, transparent 50%),
            linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }

    .hero {
        margin-bottom: 1.25rem;
    }

    .hero-title {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 760;
        color: #0f172a;
        letter-spacing: -0.03em;
    }

    .hero-sub {
        margin: 0.35rem 0 0 0;
        color: #64748b;
        font-size: 0.95rem;
    }

    .panel-title {
        margin: 0 0 0.35rem 0;
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }

    .panel-title::before {
        content: "";
        width: 4px;
        height: 1.05rem;
        border-radius: 999px;
        background: #2563eb;
        display: inline-block;
    }

    .muted {
        color: #94a3b8;
        font-size: 0.88rem;
        margin: 0.25rem 0 0.8rem 0;
    }

    .stat-row {
        display: flex;
        gap: 0.6rem;
        margin: 0.6rem 0 0.9rem 0;
        flex-wrap: wrap;
    }

    .stat-chip {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #475569;
        border-radius: 999px;
        padding: 0.28rem 0.7rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .loading-box {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 0.8rem 0;
        padding: 0.9rem 1rem;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 12px;
    }

    .loading-text {
        color: #1e40af;
        font-size: 0.92rem;
        font-weight: 600;
    }

    .spinner {
        width: 20px;
        height: 20px;
        border: 3px solid #bfdbfe;
        border-top-color: #2563eb;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        flex-shrink: 0;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .log-panel {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.85rem 0.95rem;
        margin: 0.75rem 0 1rem 0;
        max-height: 280px;
        overflow-y: auto;
    }

    .log-panel-title {
        margin: 0 0 0.65rem 0;
        color: #0f172a;
        font-size: 0.88rem;
        font-weight: 700;
    }

    .log-list {
        list-style: none;
        margin: 0;
        padding: 0;
    }

    .log-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 0.55rem 0.65rem;
        border-radius: 8px;
        margin-bottom: 0.4rem;
        font-size: 0.84rem;
        line-height: 1.4;
        color: #334155;
    }

    .log-item:last-child { margin-bottom: 0; }
    .log-item.success { background: #ecfdf5; border: 1px solid #a7f3d0; }
    .log-item.skip { background: #fff7ed; border: 1px solid #fed7aa; }
    .log-item.error { background: #fef2f2; border: 1px solid #fecaca; }
    .log-item.done {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        font-weight: 650;
        color: #1e40af;
    }
    .log-icon { flex-shrink: 0; width: 1rem; text-align: center; }

    .file-row {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.85rem 0.95rem;
        margin-bottom: 0.7rem;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    .file-row:hover {
        border-color: #cbd5e1;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    }

    .file-row-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.75rem;
    }

    .file-name {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0f172a;
        word-break: break-all;
    }

    .result-tag {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.22rem 0.65rem;
        font-size: 0.75rem;
        font-weight: 700;
        white-space: nowrap;
        flex-shrink: 0;
    }

    .result-tag.success { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
    .result-tag.skip { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
    .result-tag.error { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
    .result-tag.pending { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }

    .detail-box {
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px dashed #e2e8f0;
    }

    .detail-row {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.35rem 0;
        font-size: 0.86rem;
    }

    .detail-label { color: #64748b; }
    .detail-value {
        color: #0f172a;
        font-weight: 600;
        text-align: right;
        word-break: break-all;
        max-width: 70%;
    }

    .empty-right {
        height: 360px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #94a3b8;
        font-size: 0.95rem;
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        background: #f8fafc;
    }

    div[data-testid="stFileUploader"] {
        background: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 1.1rem 0.8rem;
    }

    div[data-testid="stFileUploader"]:hover {
        border-color: #93c5fd;
    }

    div[data-testid="stButton"] > button {
        border-radius: 10px;
        font-weight: 600;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def read_uploaded_text(uploaded_file) -> str:
    """解析上传文件为文本（支持多种格式）。"""
    return extract_text_from_upload(uploaded_file)


def init_session_state() -> None:
    defaults = {
        "pending_files": [],
        "uploaded_files": [],
        "detail_expanded": {},
        "content_expanded": {},
        "staged_keys": set(),
        "is_uploading": False,
        "upload_queue": [],
        "upload_total": 0,
        "upload_logs": [],
        "file_uploader_key": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_file_uploader() -> None:
    st.session_state.file_uploader_key += 1


def make_file_id(name: str, size: int, content: str) -> str:
    return f"{name}::{size}::{len(content)}"


def process_to_knowledge_base(content: str, filename: str) -> dict:
    """提取文本 → 大模型整理 → 写入向量库。"""
    try:
        return ingest_uploaded_document(
            content,
            filename=filename,
            uploader=DEFAULT_UPLOADER,
            refine_with_llm=True,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "skipped": False,
            "message": f"知识库处理失败：{exc}",
            "content_hash": None,
            "chunk_count": 0,
        }


def stage_files_from_uploader(uploaded_files) -> int:
    added = 0
    existing_ids = {item["id"] for item in st.session_state.pending_files}
    existing_ids.update(item["id"] for item in st.session_state.uploaded_files)
    existing_ids.update(item["id"] for item in st.session_state.upload_queue)

    for uploaded_file in uploaded_files:
        try:
            content = read_uploaded_text(uploaded_file)
        except Exception as exc:  # noqa: BLE001
            st.toast(f"{uploaded_file.name} 解析失败：{exc}", icon="⚠️")
            continue

        file_id = make_file_id(uploaded_file.name, uploaded_file.size, content)
        if file_id in st.session_state.staged_keys or file_id in existing_ids:
            continue

        file_name = uploaded_file.name
        file_ext = file_name.rsplit(".", 1)[-1].upper() if "." in file_name else "未知"
        st.session_state.pending_files.append(
            {
                "id": file_id,
                "name": file_name,
                "ext": file_ext,
                "size": uploaded_file.size,
                "size_text": format_file_size(uploaded_file.size),
                "content": content,
            }
        )
        st.session_state.staged_keys.add(file_id)
        existing_ids.add(file_id)
        added += 1
    return added


def remove_pending_file(file_id: str) -> None:
    st.session_state.pending_files = [
        item for item in st.session_state.pending_files if item["id"] != file_id
    ]
    st.session_state.staged_keys.discard(file_id)
    st.session_state.detail_expanded.pop(file_id, None)
    st.session_state.content_expanded.pop(file_id, None)


def remove_uploaded_file(file_id: str) -> None:
    st.session_state.uploaded_files = [
        item for item in st.session_state.uploaded_files if item["id"] != file_id
    ]
    st.session_state.staged_keys.discard(file_id)
    st.session_state.detail_expanded.pop(file_id, None)
    st.session_state.content_expanded.pop(file_id, None)


def clear_pending_files() -> None:
    for item in st.session_state.pending_files:
        st.session_state.staged_keys.discard(item["id"])
        st.session_state.detail_expanded.pop(item["id"], None)
        st.session_state.content_expanded.pop(item["id"], None)
    st.session_state.pending_files = []
    reset_file_uploader()


def clear_uploaded_files() -> None:
    for item in st.session_state.uploaded_files:
        st.session_state.staged_keys.discard(item["id"])
        st.session_state.detail_expanded.pop(item["id"], None)
        st.session_state.content_expanded.pop(item["id"], None)
    st.session_state.uploaded_files = []
    st.session_state.upload_logs = []
    reset_file_uploader()


def start_serial_upload() -> None:
    if not st.session_state.pending_files:
        return
    st.session_state.upload_queue = list(st.session_state.pending_files)
    st.session_state.upload_total = len(st.session_state.upload_queue)
    st.session_state.upload_logs = []
    st.session_state.pending_files = []
    st.session_state.is_uploading = True


def show_loading(filename: str, index: int, total: int) -> str:
    safe_name = html.escape(filename)
    return f"""
    <div class="loading-box">
        <div class="spinner"></div>
        <span class="loading-text">正在整理并入库：{safe_name}（{index}/{total}）</span>
    </div>
    """


def render_upload_logs_html(logs: list) -> str:
    if not logs:
        return ""

    icon_map = {
        "success": ("✓", "success"),
        "skip": ("i", "skip"),
        "error": ("!", "error"),
        "done": ("★", "done"),
    }
    items_html = []
    for log in logs:
        if isinstance(log, str):
            status, text = "success", log
        else:
            status = log.get("status", "success")
            text = log.get("text", "")
        icon, css = icon_map.get(status, ("•", "success"))
        items_html.append(
            f'<li class="log-item {css}">'
            f'<span class="log-icon">{icon}</span>'
            f"<span>{html.escape(text)}</span>"
            f"</li>"
        )

    return (
        '<div class="log-panel">'
        '<p class="log-panel-title">处理进度</p>'
        f'<ul class="log-list">{"".join(items_html)}</ul>'
        "</div>"
    )


def get_result_meta(file_item: dict, *, pending: bool) -> tuple[str, str, str]:
    """返回 (tag_class, tag_text, result_text)。"""
    if pending:
        return "pending", "待上传", "等待写入知识库"

    kb_result = file_item.get("kb_result") or {}
    if kb_result.get("success") and kb_result.get("skipped"):
        return "skip", "已存在", kb_result.get("message", "内容已存在，已跳过")
    if kb_result.get("success"):
        return "success", "上传成功", kb_result.get("message", "已写入知识库")
    return "error", "处理失败", kb_result.get("message", "处理失败")


def process_next_queued_file() -> None:
    queue = st.session_state.upload_queue
    if not queue:
        st.session_state.is_uploading = False
        return

    total = st.session_state.upload_total
    current_index = total - len(queue) + 1
    file_item = queue[0]
    file_name = file_item["name"]

    loading_placeholder = st.empty()
    log_placeholder = st.empty()

    loading_placeholder.markdown(
        show_loading(file_name, current_index, total),
        unsafe_allow_html=True,
    )
    if st.session_state.upload_logs:
        log_placeholder.markdown(
            render_upload_logs_html(st.session_state.upload_logs),
            unsafe_allow_html=True,
        )

    kb_result = process_to_knowledge_base(file_item["content"], file_name)
    kb_result["name"] = file_name

    st.session_state.upload_queue = queue[1:]
    st.session_state.uploaded_files.append({**file_item, "kb_result": kb_result})

    if kb_result.get("success") and kb_result.get("skipped"):
        tip = f"{file_name} 文件已存在，正在处理下一个文件"
        status = "skip"
        st.toast(tip, icon="ℹ️")
    elif kb_result.get("success"):
        tip = f"{file_name} 文件上传成功"
        status = "success"
        st.toast(tip, icon="✅")
    else:
        tip = f"{file_name} 文件上传失败：{kb_result.get('message', '')}"
        status = "error"
        st.toast(tip, icon="⚠️")

    st.session_state.upload_logs.append({"status": status, "text": tip})

    if st.session_state.upload_queue:
        st.rerun()

    done_msg = "所有文件已处理完成"
    st.session_state.upload_logs.append({"status": "done", "text": done_msg})
    st.toast(done_msg, icon="🎉")
    st.session_state.is_uploading = False
    loading_placeholder.empty()
    log_placeholder.markdown(
        render_upload_logs_html(st.session_state.upload_logs),
        unsafe_allow_html=True,
    )
    st.rerun()


def render_compact_file_row(file_item: dict, *, pending: bool = False) -> None:
    """右侧简略卡片：默认只显示文件名 + 处理结果，可展开详细信息。"""
    file_id = file_item["id"]
    prefix = "pending" if pending else "done"
    detail_open = st.session_state.detail_expanded.get(file_id, False)
    content_open = st.session_state.content_expanded.get(file_id, False)

    tag_class, tag_text, result_text = get_result_meta(file_item, pending=pending)
    safe_name = html.escape(file_item["name"])
    safe_result = html.escape(result_text)

    st.markdown(
        f"""
        <div class="file-row">
            <div class="file-row-top">
                <div class="file-name">{safe_name}</div>
                <span class="result-tag {tag_class}">{tag_text}</span>
            </div>
            <div style="margin-top:0.35rem;color:#64748b;font-size:0.82rem;">{safe_result}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    btn_cols = st.columns([2, 1, 1] if not pending else [2, 1])
    with btn_cols[0]:
        detail_label = "收起详细信息" if detail_open else "详细信息"
        if st.button(
            detail_label,
            key=f"detail_{prefix}_{file_id}",
            use_container_width=True,
            disabled=st.session_state.is_uploading,
        ):
            st.session_state.detail_expanded[file_id] = not detail_open
            st.rerun()
    with btn_cols[1]:
        if st.button(
            "删除",
            key=f"remove_{prefix}_{file_id}",
            use_container_width=True,
            disabled=st.session_state.is_uploading,
        ):
            if pending:
                remove_pending_file(file_id)
            else:
                remove_uploaded_file(file_id)
            st.rerun()

    if detail_open:
        kb_result = file_item.get("kb_result") or {}
        content = file_item.get("content", "")
        needs_toggle = len(content) > PREVIEW_CHARS
        display_text = (
            content[:PREVIEW_CHARS] + "…"
            if needs_toggle and not content_open
            else content
        )

        st.markdown(
            f"""
            <div class="detail-box">
                <div class="detail-row">
                    <span class="detail-label">文件格式</span>
                    <span class="detail-value">{html.escape(file_item.get("ext", "-"))}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">文件大小</span>
                    <span class="detail-value">{html.escape(file_item.get("size_text", "-"))}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">分段数量</span>
                    <span class="detail-value">{kb_result.get("chunk_count", "-") if not pending else "-"}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">SHA256</span>
                    <span class="detail-value">{html.escape(str(kb_result.get("content_hash") or "-"))}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("文件内容预览")
        st.text_area(
            f"内容-{prefix}-{file_id}",
            value=display_text,
            height=180 if not content_open else 320,
            disabled=True,
            label_visibility="collapsed",
        )
        if needs_toggle:
            content_label = "收起全文" if content_open else "展开全文"
            if st.button(
                content_label,
                key=f"content_{prefix}_{file_id}",
                use_container_width=True,
                disabled=st.session_state.is_uploading,
            ):
                st.session_state.content_expanded[file_id] = not content_open
                st.rerun()


# ---------- 页面内容 ----------
def render_upload_page() -> None:
    """渲染知识上传页（可由 app.py 调用）。"""
    _inject_upload_styles()
    render_nav("upload")
    init_session_state()

    st.markdown(
        """
        <div class="hero">
            <p class="hero-title">知识库文档上传</p>
            <p class="hero-sub">支持多种格式 → 大模型总结整理 → 写入本地向量库</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([5, 7], gap="large")

    with left_col:
        st.markdown('<p class="panel-title">上传与进度</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="muted">支持 pdf / docx / xlsx / pptx / txt / md / csv 等；上传后会先交给大模型整理，再入库。</p>',
            unsafe_allow_html=True,
        )

        # 上传进行中：在左侧显示动画，并串行处理下一个文件
        if st.session_state.is_uploading and st.session_state.upload_queue:
            process_next_queued_file()

        uploaded_files = st.file_uploader(
            "选择或拖拽 TXT 文件到此处",
            type=ALLOWED_UPLOAD_EXTENSIONS,
            accept_multiple_files=True,
            help="可多选；支持多种常见文档格式；选择后仅临时记录",
            label_visibility="collapsed",
            disabled=st.session_state.is_uploading,
            key=f"file_uploader_{st.session_state.file_uploader_key}",
        )

        if uploaded_files and not st.session_state.is_uploading:
            added = stage_files_from_uploader(uploaded_files)
            if added > 0:
                st.toast(f"已临时记录 {added} 个文件", icon="📝")

        pending_files = st.session_state.pending_files
        done_files = st.session_state.uploaded_files

        st.markdown(
            f"""
            <div class="stat-row">
                <span class="stat-chip">待上传 {len(pending_files)}</span>
                <span class="stat-chip">已处理 {len(done_files)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if pending_files:
            c1, c2 = st.columns([3, 2])
            with c1:
                if st.button(
                    "开始整理并入库",
                    use_container_width=True,
                    type="primary",
                    disabled=st.session_state.is_uploading,
                ):
                    start_serial_upload()
                    st.rerun()
            with c2:
                if st.button(
                    "清空待上传",
                    use_container_width=True,
                    disabled=st.session_state.is_uploading,
                ):
                    clear_pending_files()
                    st.rerun()

        if st.session_state.upload_logs and not st.session_state.is_uploading:
            st.markdown(
                render_upload_logs_html(st.session_state.upload_logs),
                unsafe_allow_html=True,
            )

        if done_files:
            if st.button(
                "清空已处理列表",
                use_container_width=True,
                disabled=st.session_state.is_uploading,
            ):
                clear_uploaded_files()
                st.rerun()

        if not pending_files and not done_files and not st.session_state.is_uploading:
            st.caption("请先选择一个或多个 .txt 文件。")

    with right_col:
        st.markdown('<p class="panel-title">文件信息</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="muted">默认显示文件名与处理结果，点击“详细信息”可展开更多内容。</p>',
            unsafe_allow_html=True,
        )

        pending_files = st.session_state.pending_files
        done_files = st.session_state.uploaded_files

        if not pending_files and not done_files:
            st.markdown(
                '<div class="empty-right">暂无文件，上传后将在这里展示</div>',
                unsafe_allow_html=True,
            )
        else:
            if pending_files:
                st.caption(f"待上传（{len(pending_files)}）")
                for file_item in pending_files:
                    render_compact_file_row(file_item, pending=True)

            if done_files:
                st.caption(f"已处理（{len(done_files)}）")
                for file_item in done_files:
                    render_compact_file_row(file_item, pending=False)


if __name__ == "__main__":
    from page_nav import ensure_page_state

    st.set_page_config(
        page_title="知识库文档上传",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    ensure_page_state(default="upload")
    if st.session_state.current_page == "qa":
        from app_qa import render_qa_page

        render_qa_page()
    else:
        render_upload_page()
