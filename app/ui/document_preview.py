"""
document_preview.py — 中间文档预览 UI 模块。
Phase 4：支持节点预览 / 全文预览切换。
只负责渲染，不做业务逻辑。
"""
from __future__ import annotations

import streamlit as st

from app.core.session import ReportSession
from app.core.document_service import build_node_markdown, build_full_markdown

_MODE_LABELS = ["节点预览", "全文预览"]
_MODE_KEYS   = ["node",    "full"]


def render_document_preview(session: ReportSession) -> None:
    """渲染文档预览区，支持节点预览 / 全文预览切换。"""
    # --- 标题 + 切换控件（同行布局）---
    col_title, col_toggle = st.columns([3, 2])
    with col_title:
        st.header("文档预览", divider="gray")
    with col_toggle:
        st.write("")  # 垂直对齐占位
        current_idx = _MODE_KEYS.index(session.preview_mode) if session.preview_mode in _MODE_KEYS else 0
        selected = st.radio(
            label="预览范围",
            options=_MODE_LABELS,
            index=current_idx,
            horizontal=True,
            label_visibility="collapsed",
            key="preview_mode_radio",
        )
        new_mode = _MODE_KEYS[_MODE_LABELS.index(selected)]
        if new_mode != session.preview_mode:
            session.preview_mode = new_mode
            st.session_state["report_session"] = session
            st.rerun()

    # --- 预览内容 ---
    with st.container(height=580, border=False):
        if session.preview_mode == "full":
            content = build_full_markdown(session)
        else:
            content = build_node_markdown(session, session.selected_node)
        st.markdown(content)
