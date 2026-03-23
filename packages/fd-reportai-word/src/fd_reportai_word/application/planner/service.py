from __future__ import annotations

from ...domain import GenerationPlan, ReportTemplate


class DefaultPlanner:
    def plan(self, template: ReportTemplate) -> GenerationPlan:
        sections = [section for section in template.sections if section.enabled]
        return GenerationPlan(
            template_key=template.key,
            template_version=template.version,
            sections=sections,
            options=dict(template.options),
        )
