"""
document_service.py — Phase 4：文档预览业务逻辑层。

纯 Python，不依赖 Streamlit 或 LangGraph。
Phase 5 起：build_node_markdown 将被 fd_reportai_word 生成结果替换。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.session import ReportSession

_EMPTY_PLACEHOLDERS = {"_暂无预览内容_", "_暂无字段内容_", ""}


def build_node_markdown(session: "ReportSession", node_key: str | None) -> str:
    """
    返回指定节点的 markdown 预览。
    优先使用 session.markdown[node_key]（字段保存后已更新）；
    若为空则动态构建后返回。
    """
    if node_key is None:
        return "_请在左侧选择一个节点以预览内容_"

    current = session.markdown.get(node_key, "")
    if current and current not in _EMPTY_PLACEHOLDERS:
        return current

    # 动态构建兜底
    session.rebuild_preview_from_fields(node_key)
    return session.markdown.get(node_key, "_暂无预览内容_")


def build_full_markdown(session: "ReportSession") -> str:
    """
    按 template_tree 顺序（DFS）拼接所有节点的 markdown，
    生成完整文档预览。节与节之间插入水平分割线。
    空内容节点静默跳过。
    """
    if not session.template_tree:
        return "_模版结构为空，无法生成全文预览_"

    parts: list[str] = []
    _collect_parts(session, session.template_tree, parts)
    return "\n\n---\n\n".join(parts) if parts else "_暂无内容_"


def _collect_parts(
    session: "ReportSession",
    nodes: list[dict],
    parts: list[str],
) -> None:
    for node in nodes:
        key = node["key"]
        md = build_node_markdown(session, key)
        if md and md not in _EMPTY_PLACEHOLDERS:
            parts.append(md)
        children = node.get("children") or []
        if children:
            _collect_parts(session, children, parts)
