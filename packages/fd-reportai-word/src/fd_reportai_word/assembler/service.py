from __future__ import annotations

from ..domain import BlockResult, PlannedSection, ReportDocument, ReportSectionDocument


class DefaultAssembler:
    def assemble(
        self,
        *,
        title: str,
        template_key: str,
        template_version: str,
        sections: list[PlannedSection],
        block_results: dict[tuple[str, str], BlockResult],
        blocked_items: list[dict[str, str]],
        metadata: dict[str, object] | None = None,
    ) -> ReportDocument:
        return ReportDocument(
            title=title,
            template_key=template_key,
            template_version=template_version,
            sections=[self._assemble_section(section, block_results) for section in sections],
            blocked_items=blocked_items,
            metadata=dict(metadata or {}),
        )

    def _assemble_section(
        self,
        section: PlannedSection,
        block_results: dict[tuple[str, str], BlockResult],
    ) -> ReportSectionDocument:
        return ReportSectionDocument(
            key=section.definition.key,
            title=section.definition.title,
            blocks=[block_results[(task.section_key, task.definition.key)] for task in section.tasks],
            children=[self._assemble_section(child, block_results) for child in section.children],
            options=dict(section.definition.options),
        )
