from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import WordContext
from ..domain import ReportDocument, ReportSectionDocument


class DefaultRenderer:
    def render(self, document: ReportDocument) -> dict[str, object]:
        return {
            "title": document.title,
            "template_key": document.template_key,
            "template_version": document.template_version,
            "sections": [self._render_section(section) for section in document.sections],
            "markdown": self._render_markdown(document),
            "blocked_items": list(document.blocked_items),
            "metadata": dict(document.metadata),
        }

    def _render_section(self, section: ReportSectionDocument) -> dict[str, object]:
        return {
            "key": section.key,
            "title": section.title,
            "blocks": [
                {
                    "block_key": block.block_key,
                    "title": block.title,
                    "block_type": block.block_type,
                    "generator_mode": block.generator_mode,
                    "content": block.content,
                    "trace": {
                        "template_version": block.trace.template_version,
                        "rule_version": block.trace.rule_version,
                        "prompt_version": block.trace.prompt_version,
                        "model_version": block.trace.model_version,
                        "data_snapshot_id": block.trace.data_snapshot_id,
                        "block_revision": block.trace.block_revision,
                        "input_snapshot": dict(block.trace.input_snapshot),
                    },
                    "validation": {
                        "is_valid": block.validation.is_valid,
                        "issues": [
                            {
                                "code": issue.code,
                                "message": issue.message,
                                "severity": issue.severity,
                            }
                            for issue in block.validation.issues
                        ],
                    },
                }
                for block in section.blocks
            ],
            "children": [self._render_section(child) for child in section.children],
            "options": dict(section.options),
        }

    def _render_markdown(self, document: ReportDocument) -> str:
        parts = [f"# {document.title}"]
        for section in document.sections:
            section_markdown = self._render_markdown_section(section, level=2)
            if section_markdown:
                parts.append(section_markdown)
        return "\n\n".join(parts).strip()

    def _render_markdown_section(self, section: ReportSectionDocument, level: int) -> str:
        heading = f"{'#' * max(level, 1)} {section.title}"
        parts = [heading]

        for block in section.blocks:
            content = self._render_markdown_content(block.content)
            if content:
                parts.append(content)

        for child in section.children:
            child_markdown = self._render_markdown_section(child, level + 1)
            if child_markdown:
                parts.append(child_markdown)

        return "\n\n".join(parts).strip()

    def _render_markdown_content(self, content: object) -> str:
        if isinstance(content, dict):
            content_type = content.get("type")
            if content_type == "rich_text":
                return str(content.get("text", "")).strip()
            if content_type == "table":
                return self._render_markdown_table(content)
            if content_type == "image_group":
                items = content.get("items", [])
                return "\n".join(f"- {item}" for item in items) if isinstance(items, list) else str(items)
            return str(content.get("content", "")).strip()
        return str(content).strip()

    def _render_markdown_table(self, content: dict[str, object]) -> str:
        rows = content.get("rows", [])
        if not isinstance(rows, list) or not rows:
            return ""

        if all(isinstance(row, dict) for row in rows):
            headers = list(rows[0].keys())
            header_row = "| " + " | ".join(str(header) for header in headers) + " |"
            separator_row = "| " + " | ".join("---" for _ in headers) + " |"
            data_rows = [
                "| " + " | ".join(str(row.get(header, "")) for header in headers) + " |"
                for row in rows
            ]
            return "\n".join([header_row, separator_row, *data_rows])

        data_rows = []
        for row in rows:
            if isinstance(row, (list, tuple)):
                data_rows.append("| " + " | ".join(str(cell) for cell in row) + " |")
            else:
                data_rows.append(f"- {row}")
        return "\n".join(data_rows)


class BaseRenderer(ABC):
    @abstractmethod
    def render(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopRenderer(BaseRenderer):
    def render(self, context: WordContext) -> None:
        if context.composed_document is None:
            context.rendered_output = None
            return
        context.rendered_output = DefaultRenderer().render(context.composed_document)
