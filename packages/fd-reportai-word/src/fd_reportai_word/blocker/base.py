from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import WordContext
from ..domain import (
    BlockTask,
    DataContext,
    DefinitionInput,
    ElementValue,
    GenerationPlan,
    PlannedSection,
    ResolvedInput,
    SectionDefinition,
)


class DefaultBlocker:
    def build(
        self,
        plan: GenerationPlan,
        data_context: DataContext,
    ) -> tuple[list[PlannedSection], list[dict[str, str]]]:
        planned_sections = [self._build_section(section, data_context) for section in plan.sections]
        blocked_items = self._collect_blocked_items(planned_sections)
        return planned_sections, blocked_items

    def _build_section(
        self,
        section: SectionDefinition,
        data_context: DataContext,
    ) -> PlannedSection:
        tasks = [
            BlockTask(
                section_key=section.key,
                section_title=section.title,
                definition=block,
                resolved_inputs=self._resolve_inputs(block.inputs, data_context),
                options=dict(block.options),
            )
            for block in section.blocks
        ]
        for task in tasks:
            task.missing_required_inputs = [
                resolved.key
                for resolved in task.resolved_inputs
                if resolved.required and not resolved.has_value
            ]

        children = [self._build_section(child, data_context) for child in section.children if child.enabled]
        return PlannedSection(definition=section, tasks=tasks, children=children)

    def _resolve_inputs(
        self,
        definitions: list[DefinitionInput],
        data_context: DataContext,
    ) -> list[ResolvedInput]:
        resolved_inputs: list[ResolvedInput] = []
        for definition in definitions:
            source_key, element = self._find_element_for_definition(definition, data_context)
            has_value = element is not None
            used_default = not has_value and definition.default_value is not None
            resolved_inputs.append(
                ResolvedInput(
                    key=definition.key,
                    source_key=source_key,
                    required=definition.required,
                    value=element.value if has_value else definition.default_value,
                    has_value=has_value or used_default,
                    used_default=used_default,
                    options=dict(definition.options),
                )
            )
        return resolved_inputs

    def _find_element_for_definition(
        self,
        definition: DefinitionInput,
        data_context: DataContext,
    ) -> tuple[str, ElementValue | None]:
        candidate_keys = [definition.source_key or definition.key, *definition.aliases]
        for candidate_key in candidate_keys:
            element = data_context.values.get(candidate_key)
            if element is not None:
                return candidate_key, element
            extracted = self._extract_element_from_path(candidate_key, data_context)
            if extracted is not None:
                transformed = self._apply_transform(extracted, definition.options.get("transform"))
                return candidate_key, ElementValue(value=transformed)
        return definition.source_key or definition.key, None

    def _extract_element_from_path(self, path: str, data_context: DataContext) -> object | None:
        if "." not in path and "[" not in path:
            return None
        current: object | None = data_context.values
        for part in path.split("."):
            if current is None:
                return None
            current = self._resolve_path_part(current, part)
        if isinstance(current, ElementValue):
            return current.value
        return current

    def _resolve_path_part(self, current: object, part: str) -> object | None:
        token = part.strip()
        if not token:
            return current
        while token:
            if "[" in token:
                field_name, rest = token.split("[", 1)
                if field_name:
                    current = self._resolve_mapping_value(current, field_name)
                index_text, remainder = rest.split("]", 1)
                if not isinstance(current, list):
                    return None
                try:
                    current = current[int(index_text)]
                except (ValueError, IndexError):
                    return None
                token = remainder
            else:
                current = self._resolve_mapping_value(current, token)
                token = ""
        return current

    def _resolve_mapping_value(self, current: object, key: str) -> object | None:
        if isinstance(current, ElementValue):
            current = current.value
        if isinstance(current, dict):
            return current.get(key)
        return None

    def _apply_transform(self, value: object | None, transform: object) -> object | None:
        if value is None or transform is None:
            return value
        if transform == "cn_date":
            return self._to_chinese_date(str(value))
        raise ValueError(f"Unsupported transform: {transform}.")

    def _to_chinese_date(self, value: str) -> str:
        import re

        match = re.fullmatch(r"\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*", value)
        if not match:
            return value
        year, month, day = match.groups()
        digits = {"0": "〇", "1": "一", "2": "二", "3": "三", "4": "四", "5": "五", "6": "六", "7": "七", "8": "八", "9": "九"}
        return f"{''.join(digits[ch] for ch in year)}年{self._to_chinese_number(int(month))}月{self._to_chinese_number(int(day))}日"

    def _to_chinese_number(self, value: int) -> str:
        digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
        if value < 10:
            return digits[value]
        if value == 10:
            return "十"
        if value < 20:
            return "十" + digits[value % 10]
        tens, ones = divmod(value, 10)
        if ones == 0:
            return digits[tens] + "十"
        return digits[tens] + "十" + digits[ones]

    def _collect_blocked_items(self, sections: list[PlannedSection]) -> list[dict[str, str]]:
        blocked_items: list[dict[str, str]] = []
        for section in sections:
            for task in section.tasks:
                for missing in task.missing_required_inputs:
                    blocked_items.append(
                        {
                            "section_key": task.section_key,
                            "block_key": task.definition.key,
                            "missing_input": missing,
                        }
                    )
            blocked_items.extend(self._collect_blocked_items(section.children))
        return blocked_items


class BaseBlocker(ABC):
    @abstractmethod
    def block(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopBlocker(BaseBlocker):
    def block(self, context: WordContext) -> None:
        if context.plan is None:
            context.planned_sections = []
            context.blocked_items = []
            return
        context.data_context = DataContext(
            values=dict(context.elements),
            metadata=dict(context.metadata),
            snapshot_id=context.metadata.get("data_snapshot_id"),
        )
        context.planned_sections, context.blocked_items = DefaultBlocker().build(
            context.plan,
            context.data_context,
        )
        computed_field_keys = {field.key for field in (context.template.computed_fields if context.template else [])}
        if not computed_field_keys:
            return
        self._clear_computable_missing_inputs(context.planned_sections, computed_field_keys)
        context.blocked_items = DefaultBlocker()._collect_blocked_items(context.planned_sections)

    def _clear_computable_missing_inputs(
        self,
        sections: list[PlannedSection],
        computed_field_keys: set[str],
    ) -> None:
        for section in sections:
            for task in section.tasks:
                task.missing_required_inputs = [
                    resolved.key
                    for resolved in task.resolved_inputs
                    if resolved.required
                    and not resolved.has_value
                    and resolved.source_key not in computed_field_keys
                ]
            self._clear_computable_missing_inputs(section.children, computed_field_keys)
