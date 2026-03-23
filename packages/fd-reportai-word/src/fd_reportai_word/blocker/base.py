from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import WordContext


class BaseBlocker(ABC):
    @abstractmethod
    def block(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopBlocker(BaseBlocker):
    def block(self, context: WordContext) -> None:
        context.execution_blocks = self._build_blocks(context.plan, context)
        context.blocked_items = [
            {
                "section_key": block["section_key"],
                "missing_element": missing_element,
            }
            for block in context.execution_blocks
            for missing_element in block["missing_required_elements"]
        ]

    def _build_blocks(
        self,
        planned_sections: list[dict[str, object]],
        context: WordContext,
    ) -> list[dict[str, object]]:
        return [self._build_block(section, context) for section in planned_sections]

    def _build_block(
        self,
        planned_section: dict[str, object],
        context: WordContext,
    ) -> dict[str, object]:
        resolved_elements: list[dict[str, object]] = []
        missing_required_elements: list[str] = []

        for element in planned_section.get("elements", []):
            source_key = str(element["source_key"])
            is_required = bool(element["required"])
            has_default = bool(element["has_default"])
            has_value = source_key in context.elements
            default_value = element.get("default_value")
            element_input = context.elements.get(source_key)
            if is_required and not has_default and not has_value:
                missing_required_elements.append(str(element["key"]))

            resolved_elements.append(
                {
                    "key": str(element["key"]),
                    "source_key": source_key,
                    "required": is_required,
                    "has_value": has_value,
                    "value": element_input.value if element_input else default_value,
                    "input": element_input,
                }
            )

        children = [
            self._build_block(child, context) for child in planned_section.get("children", [])
        ]

        return {
            "section_key": str(planned_section["section_key"]),
            "title": str(planned_section["title"]),
            "block_mode": str(planned_section["block_mode"]),
            "template": planned_section.get("template"),
            "prompt": planned_section.get("prompt"),
            "few_shots": list(planned_section.get("few_shots", [])),
            "elements": resolved_elements,
            "missing_required_elements": missing_required_elements,
            "children": children,
            "options": dict(planned_section.get("options", {})),
        }
