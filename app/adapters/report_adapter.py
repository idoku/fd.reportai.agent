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
    """从 pipeline 结果中提取各章节的 markdown 文本。"""
    _ensure_package_on_path()
    from fd_reportai_word.renderer.base import DefaultRenderer  # noqa: PLC0415

    result: dict[str, str] = {}
    composed = getattr(context, "composed_document", None)
    if composed is None:
        return result

    renderer = DefaultRenderer()
    for section in composed.sections:
        md = renderer._render_markdown_section(section, level=2)
        if md:
            result[section.key] = md
            # 同步更新 content_items（子节点）的 markdown
            for child in (section.children or []):
                child_md = renderer._render_markdown_section(child, level=3)
                if child_md:
                    result[child.key] = child_md

    return result
