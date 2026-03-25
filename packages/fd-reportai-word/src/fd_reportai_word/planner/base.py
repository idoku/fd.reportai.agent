from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import WordContext
from ..domain import GenerationPlan, ReportTemplate


class DefaultPlanner:
    def plan(self, template: ReportTemplate) -> GenerationPlan:
        sections = [section for section in template.sections if section.enabled]
        return GenerationPlan(
            template_key=template.key,
            template_version=template.version,
            sections=sections,
            options=dict(template.options),
        )


class BasePlanner(ABC):
    @abstractmethod
    def plan(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopPlanner(BasePlanner):
    def plan(self, context: WordContext) -> None:
        if context.framework is None:
            context.plan = None
            return
        context.template = context.framework.to_report_template()
        context.plan = DefaultPlanner().plan(context.template)
