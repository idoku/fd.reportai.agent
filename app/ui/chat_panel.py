"""
chat_panel.py — 下方对话面板 UI 模块。
Phase 1：仅渲染聊天记录、接收用户输入（追加到 session）。
文件上传按钮为 stub，Phase 7 实现实际解析。
"""
from __future__ import annotations

import streamlit as st

from app.core.session import ReportSession

_STUB_REPLY = "（AI 对话将在 Phase 6 接入，当前为 stub 回复）"


def render_chat_panel(session: ReportSession) -> None:
    """渲染聊天区：历史记录 + 输入框 + 文件上传 stub。"""
    st.subheader("对话", divider="gray")

    # --- 聊天记录 ---
    chat_container = st.container(height=260, border=False)
    with chat_container:
        if not session.chat_history:
            st.caption("_暂无对话记录，请在下方输入内容开始对话_")
        for msg in session.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # --- 文件上传 stub（Phase 7 实现解析）---
    uploaded = st.file_uploader(
        label="📎 上传附件（Phase 7 实现）",
        label_visibility="visible",
        key="chat_file_upload",
        accept_multiple_files=False,
    )
    if uploaded is not None:
        st.caption(f"已选择：{uploaded.name}（Phase 7 实现解析）")

    # --- 聊天输入（必须在顶层，不能放在 st.columns 内）---
    user_input = st.chat_input(placeholder="输入你的需求，例如：修改报告编号…")

    if user_input:
        session.add_chat_message("user", user_input)
        # Phase 1 stub：自动回复占位消息
        session.add_chat_message("assistant", _STUB_REPLY)
        st.session_state["report_session"] = session
        st.rerun()
