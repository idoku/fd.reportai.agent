"""
config_loader.py — Phase 2：从 fd_reportai_word 读取真实模版结构。

load_template_nodes() 优先从 fd_reportai_word.RULESET_LAND 读取 section 层级，
ImportError / 任何异常时自动回退到 mock 数据，保证页面始终可用。
"""
from __future__ import annotations

from app.core.mock_data import MOCK_TEMPLATE_TREE


def load_template_nodes(ruleset_name: str = "ruleset_land") -> list[dict]:
    """
    返回模版节点列表，每项结构：{key, title, children: list[dict]}。
    优先从 fd_reportai_word 加载；失败时回退到 MOCK_TEMPLATE_TREE。
    """
    try:
        from fd_reportai_word import get_default_ruleset  # noqa: PLC0415

        ruleset = get_default_ruleset(ruleset_name)
        return [_section_to_node(s) for s in ruleset.sections]
    except Exception:
        return list(MOCK_TEMPLATE_TREE)


def _section_to_node(section) -> dict:
    """将 ReportSectionConfig 转换为 TemplateNode dict（两层）。"""
    children: list[dict] = []
    # 第一层：子章节（ReportSectionConfig.children）
    for c in (getattr(section, "children", None) or []):
        children.append(_section_to_node(c))
    # 第二层：内容项（ReportSectionConfig.content_items）
    for ci in (getattr(section, "content_items", None) or []):
        children.append({"key": ci.key, "title": ci.key, "children": []})
    return {
        "key": section.key,
        "title": section.title,
        "children": children,
    }
