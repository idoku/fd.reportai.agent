"""
element_panel.py — 右侧字段要素编辑面板 UI 模块。
只负责渲染，不做业务逻辑。
"""
from __future__ import annotations

import streamlit as st

from app.core.session import ReportSession


def render_element_panel(session: ReportSession) -> None:
    """渲染当前节点的字段表单，支持文本输入并实时回写 session。"""
    st.header("要素编辑", divider="gray")

    if session.selected_node is None:
        st.info("请先在左侧选择一个节点。")
        return

    fields = session.get_current_fields()
    if not fields:
        st.info("当前节点没有可编辑字段。")
        return

    with st.form(key="element_form", border=False):
        updated: dict[str, str] = {}
        for f in fields:
            updated[f["key"]] = st.text_input(
                label=f["label"],
                value=f["value"],
                key=f"field_{session.selected_node}_{f['key']}",
            )

        submitted = st.form_submit_button("保存", type="primary", use_container_width=True)
        if submitted:
            for field_key, value in updated.items():
                session.update_field(field_key, value)
            # Bug fix: 字段保存后重建中间预览内容
            session.rebuild_preview_from_fields(session.selected_node)
            st.session_state["report_session"] = session
            st.rerun()
