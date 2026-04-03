"""
document_preview.py — 中间文档预览 UI 模块。
只负责渲染，不做业务逻辑。
"""
from __future__ import annotations

import streamlit as st

from app.core.session import ReportSession


def render_document_preview(session: ReportSession) -> None:
    """渲染当前节点的 markdown 预览内容。"""
    st.header("文档预览", divider="gray")
    content = session.get_current_markdown()
    st.markdown(content)
