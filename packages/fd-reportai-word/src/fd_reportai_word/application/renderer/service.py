from __future__ import annotations

from ...domain import ReportDocument, ReportSectionDocument


class DefaultRenderer:
    def render(self, document: ReportDocument) -> dict[str, object]:
        return {
            "title": document.title,
            "template_key": document.template_key,
            "template_version": document.template_version,
            "sections": [self._render_section(section) for section in document.sections],
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
