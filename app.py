"""
app.py — Report Studio 入口。

布局：
    ┌──────────┬────────────────────┬──────────────┐
    │ sidebar  │  document_preview  │ element_panel│
    └──────────┴────────────────────┴──────────────┘
    │              chat_panel                       │
    └───────────────────────────────────────────────┘

状态统一通过 st.session_state["report_session"] 管理。
"""
import streamlit as st

from app.core.session import ReportSession, init_session
from app.ui.sidebar_tree import render_sidebar
from app.ui.document_preview import render_document_preview
from app.ui.element_panel import render_element_panel
from app.ui.chat_panel import render_chat_panel


# --------------------------------------------------------------------------- #
# 页面配置（必须是第一个 Streamlit 调用）                                       #
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="Report Studio",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------- #
# Session 初始化                                                               #
# --------------------------------------------------------------------------- #

if "report_session" not in st.session_state:
    st.session_state["report_session"] = init_session()

session: ReportSession = st.session_state["report_session"]

# --------------------------------------------------------------------------- #
# 标题栏                                                                       #
# --------------------------------------------------------------------------- #

st.title("📄 Report Studio")
st.caption("Phase 3 — 要素系统（真实字段映射）")
st.divider()

# --------------------------------------------------------------------------- #
# 三栏布局：sidebar | preview | element panel                                  #
# --------------------------------------------------------------------------- #

col_sidebar, col_preview, col_elements = st.columns([1, 3, 2], gap="medium")

with col_sidebar:
    render_sidebar(session)

with col_preview:
    render_document_preview(session)

with col_elements:
    render_element_panel(session)

# --------------------------------------------------------------------------- #
# 全宽聊天区（页面底部）                                                        #
# --------------------------------------------------------------------------- #

st.divider()
render_chat_panel(session)
