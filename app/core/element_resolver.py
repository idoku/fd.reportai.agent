"""
element_resolver.py — Phase 3：节点 → 字段映射。

resolve_all_fields()  从 fd_reportai_word.RULESET_LAND 提取每个章节的输入字段，
转换为 {key, label, value, required} 的统一字典格式供 element_panel 使用。
section.elements（顶层字段）+ content_items 中的每个 element 均会被收集，
按 key 去重，保证不重复展示同一字段。

失败时整体回退到 MOCK_FIELDS，保证任意环境下 UI 可用。
"""
from __future__ import annotations

from app.core.mock_data import MOCK_FIELDS


# --------------------------------------------------------------------------- #
# 公开 API                                                                     #
# --------------------------------------------------------------------------- #

def resolve_all_fields(ruleset_name: str = "ruleset_land") -> dict[str, list[dict]]:
    """
    返回 {section_key: [field_dict, ...]} 结构。
    field_dict 格式：{key, label, value, required}。
    优先从 fd_reportai_word 解析；失败时整体回退到 MOCK_FIELDS。
    """
    try:
        from fd_reportai_word import get_default_ruleset  # noqa: PLC0415

        ruleset = get_default_ruleset(ruleset_name)
        return {section.key: _extract_fields(section) for section in ruleset.sections}
    except Exception:
        return {k: list(v) for k, v in MOCK_FIELDS.items()}


# --------------------------------------------------------------------------- #
# 内部辅助                                                                     #
# --------------------------------------------------------------------------- #

def _extract_fields(section) -> list[dict]:
    """
    合并 section.elements 与每个 content_item.elements，按 key 去重后返回字段列表。
    顺序：section顶层字段优先，再逐个 content_item 展开。
    """
    seen: set[str] = set()
    fields: list[dict] = []

    for elem in getattr(section, "elements", None) or []:
        if elem.key not in seen:
            seen.add(elem.key)
            fields.append(_elem_to_field(elem))

    for ci in getattr(section, "content_items", None) or []:
        for elem in getattr(ci, "elements", None) or []:
            if elem.key not in seen:
                seen.add(elem.key)
                fields.append(_elem_to_field(elem))

    return fields


def _elem_to_field(elem) -> dict:
    """将 SectionElementConfig 转换为 UI 可用的字段 dict。"""
    raw_default = getattr(elem, "default_value", None)
    if raw_default is None:
        value = ""
    elif isinstance(raw_default, list):
        value = "\n".join(str(v) for v in raw_default)
    else:
        value = "" if str(raw_default) == "" else str(raw_default)

    return {
        "key": elem.key,
        "label": elem.key,        # 中文 key 本身即为友好标签
        "value": value,
        "required": getattr(elem, "required", True),
    }
