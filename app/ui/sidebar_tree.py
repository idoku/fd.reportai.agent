"""
sidebar_tree.py — 左侧节点树 UI 模块。
只负责渲染，不做业务逻辑。
"""
from __future__ import annotations

import streamlit as st

from app.core.mock_data import MOCK_TEMPLATE_TREE
from app.core.session import ReportSession


def render_sidebar(session: ReportSession) -> None:
    """渲染左侧模版节点列表，选中后更新 session.selected_node。"""
    st.header("模版结构", divider="gray")

    for node in MOCK_TEMPLATE_TREE:
        key = node["key"]
        title = node["title"]
        is_selected = session.selected_node == key

        # 用 primary 按钮高亮当前选中节点
        btn_type = "primary" if is_selected else "secondary"
        if st.button(title, key=f"nav_{key}", type=btn_type, use_container_width=True):
            session.selected_node = key
            st.session_state["report_session"] = session
            st.rerun()
