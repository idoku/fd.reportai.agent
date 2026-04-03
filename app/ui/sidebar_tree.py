"""
sidebar_tree.py — 左侧节点树 UI 模块。
只负责渲染，不做业务逻辑。
Phase 5：使用 session.template_tree，支持两层结构（章节 + 内容项）。
"""
from __future__ import annotations

import streamlit as st

from app.core.session import ReportSession


def render_sidebar(session: ReportSession) -> None:
    """渲染左侧模版节点列表，选中后更新 session.selected_node。"""
    st.header("模版结构", divider="gray")
    _render_nodes(session, session.template_tree)


def _render_nodes(session: ReportSession, nodes: list[dict], depth: int = 0) -> None:
    """递归渲染节点列表，支持两层缩进。"""
    for node in nodes:
        key = node["key"]
        title = node["title"]
        children = node.get("children") or []
        is_selected = session.selected_node == key

        btn_type = "primary" if is_selected else "secondary"
        label = f"└ {title}" if depth > 0 else title
        if st.button(label, key=f"nav_{key}", type=btn_type, use_container_width=True):
            session.selected_node = key
            st.session_state["report_session"] = session
            st.rerun()

        if children:
            _render_nodes(session, children, depth + 1)
