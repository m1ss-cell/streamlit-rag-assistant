"""本地文件会话历史：按用户 ID 读写，供 RAG prompt 注入。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from config_data import (
    DEFAULT_USER_ID,
    HISTORY_DIR,
    HISTORY_MAX_TURNS,
    UPLOAD_TIME_FORMAT,
)


def ensure_history_dir() -> Path:
    """确保历史会话目录存在。"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    return HISTORY_DIR


def _safe_user_id(user_id: str | None) -> str:
    """清洗用户 ID，避免非法文件名。"""
    uid = (user_id or DEFAULT_USER_ID).strip() or DEFAULT_USER_ID
    uid = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", uid)
    return uid


def get_history_file(user_id: str | None = None) -> Path:
    """返回指定用户的历史会话文件路径。"""
    ensure_history_dir()
    return HISTORY_DIR / f"{_safe_user_id(user_id)}.json"


def load_history(user_id: str | None = None) -> list[dict[str, Any]]:
    """
    读取用户历史会话。

    每条记录格式：
        {"role": "user"|"assistant", "content": str, "time": str}
    """
    path = get_history_file(user_id)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return data


def save_history(messages: list[dict[str, Any]], user_id: str | None = None) -> Path:
    """整表覆盖保存用户历史会话。"""
    path = get_history_file(user_id)
    path.write_text(
        json.dumps(messages, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def clear_history(user_id: str | None = None) -> None:
    """清空指定用户的历史会话。"""
    path = get_history_file(user_id)
    if path.exists():
        path.unlink()


def append_message(
    role: str,
    content: str,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """追加一条消息到历史，并写回本地文件。"""
    messages = load_history(user_id)
    messages.append(
        {
            "role": role,
            "content": (content or "").strip(),
            "time": datetime.now().strftime(UPLOAD_TIME_FORMAT),
        }
    )
    save_history(messages, user_id=user_id)
    return messages


def append_turn(
    question: str,
    answer: str,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """追加一轮完整对话（用户问题 + 助手回答）。"""
    append_message("user", question, user_id=user_id)
    return append_message("assistant", answer, user_id=user_id)


def get_recent_messages(
    user_id: str | None = None,
    max_turns: int | None = None,
) -> list[dict[str, Any]]:
    """
    获取最近 N 轮对话对应的消息列表。

    一轮 = user + assistant，因此最多取 max_turns * 2 条消息。
    """
    turns = HISTORY_MAX_TURNS if max_turns is None else max_turns
    messages = load_history(user_id)
    if turns <= 0:
        return []
    max_messages = turns * 2
    return messages[-max_messages:]


def format_history_for_prompt(
    user_id: str | None = None,
    max_turns: int | None = None,
) -> str:
    """
    将历史会话格式化为可注入 prompt 的文本。

    若无历史，返回明确占位说明。
    """
    recent = get_recent_messages(user_id=user_id, max_turns=max_turns)
    if not recent:
        return "（暂无历史会话）"

    lines: list[str] = []
    for item in recent:
        role = item.get("role", "")
        content = (item.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            lines.append(f"用户：{content}")
        elif role == "assistant":
            lines.append(f"助手：{content}")
        else:
            lines.append(f"{role}：{content}")
    return "\n".join(lines) if lines else "（暂无历史会话）"


if __name__ == "__main__":
    demo_user = DEFAULT_USER_ID
    clear_history(demo_user)
    append_turn("你好", "你好，有什么可以帮您？", user_id=demo_user)
    append_turn("衣服能机洗吗？", "根据资料，建议轻柔机洗。", user_id=demo_user)
    print("历史文件:", get_history_file(demo_user))
    print("注入文本:\n", format_history_for_prompt(demo_user))
