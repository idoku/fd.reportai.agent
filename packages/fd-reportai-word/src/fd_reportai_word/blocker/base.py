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
from ..transforms import apply_transform


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
                return candidate_key, self._transform_element_value(element, definition, data_context)

        for candidate_key in candidate_keys:
            extracted = self._find_nested_value(data_context.values, candidate_key)
            if extracted is not None:
                return candidate_key, ElementValue(
                    value=self._apply_transform(extracted, definition.options.get("transform"), data_context)
                )

        return definition.source_key or definition.key, None

    def _find_nested_value(self, current: object, target_key: str) -> object | None:
        if isinstance(current, ElementValue):
            current = current.value

        if isinstance(current, dict):
            if target_key in current:
                value = current[target_key]
                if isinstance(value, ElementValue):
                    return value.value
                return value
            for value in current.values():
                nested = self._find_nested_value(value, target_key)
                if nested is not None:
                    return nested
            return None

        if isinstance(current, list):
            for item in current:
                nested = self._find_nested_value(item, target_key)
                if nested is not None:
                    return nested

        return None

    def _transform_element_value(
        self,
        element: ElementValue,
        definition: DefinitionInput,
        data_context: DataContext,
    ) -> ElementValue:
        transform = definition.options.get("transform")
        if transform is None:
            return element
        return ElementValue(
            value=self._apply_transform(element.value, transform, data_context),
            label=element.label,
            type=element.type,
            options=dict(element.options),
        )

    def _apply_transform(self, value: object | None, transform: object, data_context: DataContext) -> object | None:
        return apply_transform(value, transform, data_context.metadata)

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
