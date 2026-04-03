"""
report_adapter.py — Phase 5：fd_reportai_word 文档生成适配器。

负责将 ReportSession 中的字段数据传入 fd_reportai_word pipeline，
调用 mock LLM 生成各章节 markdown，并将结果以 {section_key: markdown} 格式返回。

失败时静默返回空字典，保证页面不崩溃。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.session import ReportSession

_PACKAGE_SRC = Path(__file__).resolve().parents[3] / "packages" / "fd-reportai-word" / "src"


def _ensure_package_on_path() -> None:
    if str(_PACKAGE_SRC) not in sys.path:
        sys.path.insert(0, str(_PACKAGE_SRC))


def generate_section_markdown(session: "ReportSession") -> dict[str, str]:
    """
    调用 fd_reportai_word pipeline（mock LLM）生成所有章节的 markdown。

    Returns:
        {section_key: markdown_str}，仅包含成功生成的章节。
        失败时返回空字典。
    """
    _ensure_package_on_path()
    try:
        from fd_reportai_word import WordContext, WordPipeline, get_default_ruleset  # noqa: PLC0415
        from fd_reportai_word.domain import ElementValue  # noqa: PLC0415

        # 从 session.fields 汇总所有要素值（以最先出现的 key 为准，跳过空值）
        elements: dict[str, ElementValue] = {}
        for fields in session.fields.values():
            for f in fields:
                key = f["key"]
                value = f.get("value", "")
                if value and key not in elements:
                    elements[key] = ElementValue(value=value)

        context = WordContext(
            framework=get_default_ruleset("ruleset_land"),
            elements=elements,
        )
        # 不传入 locator，让 computed 字段静默跳过（返回 None），模板中保留占位符
        result = WordPipeline().run(context=context)

        return _extract_markdown_by_section(result)
    except Exception:
        return {}


# --------------------------------------------------------------------------- #
# 内部辅助                                                                     #
# --------------------------------------------------------------------------- #

def _extract_markdown_by_section(context: object) -> dict[str, str]:
    """从 pipeline 渲染结果中提取各章节的 markdown 文本。"""
    result: dict[str, str] = {}
    rendered = getattr(context, "rendered_output", None)
    if not isinstance(rendered, dict):
        return result

    for section in rendered.get("sections", []):
        key = section.get("key", "")
        if not key:
            continue
        md = _section_dict_to_markdown(section, level=2)
        if md:
            result[key] = md
        # 同步更新子节点（content_items 生成的 children）
        for child in section.get("children") or []:
            child_key = child.get("key", "")
            if not child_key:
                continue
            child_md = _section_dict_to_markdown(child, level=3)
            if child_md:
                result[child_key] = child_md

    return result


def _section_dict_to_markdown(section: dict, level: int) -> str:
    """将渲染结果中的 section 字典转换为 markdown 字符串。"""
    heading = "#" * max(level, 1) + " " + section.get("title", "")
    parts = [heading]

    for block in section.get("blocks") or []:
        content = block.get("content")
        md_content = _content_to_markdown(content)
        if md_content:
            parts.append(md_content)

    for child in section.get("children") or []:
        child_md = _section_dict_to_markdown(child, level + 1)
        if child_md:
            parts.append(child_md)

    text = "\n\n".join(parts).strip()
    return text if len(parts) > 1 else ""  # 只有标题行时跳过


def _content_to_markdown(content: object) -> str:
    """将 block content 转换为 markdown 字符串。"""
    if isinstance(content, dict):
        content_type = content.get("type")
        if content_type == "rich_text":
            return str(content.get("text", "")).strip()
        if content_type == "table":
            return _table_to_markdown(content)
        if content_type == "image_group":
            items = content.get("items", [])
            return "\n".join(f"- {item}" for item in items) if isinstance(items, list) else str(items)
        return str(content.get("content", "")).strip()
    return str(content).strip() if content is not None else ""


def _table_to_markdown(content: dict) -> str:
    """将 table content 转换为 markdown 表格。"""
    rows = content.get("rows", [])
    if not isinstance(rows, list) or not rows:
        return ""
    if all(isinstance(row, dict) for row in rows):
        headers = list(rows[0].keys())
        header_row = "| " + " | ".join(str(h) for h in headers) + " |"
        sep_row = "| " + " | ".join("---" for _ in headers) + " |"
        data_rows = [
            "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |"
            for row in rows
        ]
        return "\n".join([header_row, sep_row, *data_rows])
    return "\n".join(
        "| " + " | ".join(str(cell) for cell in row) + " |"
        if isinstance(row, (list, tuple))
        else f"- {row}"
        for row in rows
    )
