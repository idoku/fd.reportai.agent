from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import ReportSectionConfig
from ..context import WordContext


class BasePlanner(ABC):
    @abstractmethod
    def plan(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopPlanner(BasePlanner):
    def plan(self, context: WordContext) -> None:
        if context.framework is None:
            context.plan = []
            return

        context.plan = self._plan_sections(context.framework.sections)

    def _plan_sections(self, sections: list[ReportSectionConfig]) -> list[dict[str, object]]:
        plan: list[dict[str, object]] = []
        for section in sections:
            plan.append(
                {
                    "section_key": section.key,
                    "title": section.title,
                    "template": section.template,
                    "block_mode": section.block_mode,
                    "prompt": section.prompt,
                    "few_shots": section.few_shots,
                    "elements": [
                        {
                            "key": element.key,
                            "source_key": element.source_key or element.key,
                            "required": element.required,
                            "has_default": element.default_value is not None,
                            "default_value": element.default_value,
                        }
                        for element in section.elements
                    ],
                    "children": self._plan_sections(section.children),
                    "options": section.options,
                }
            )
        return plan
