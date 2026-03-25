from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import WordContext
from ..domain import (
    BlockTask,
    DataContext,
    DefinitionInput,
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
            source_key = definition.source_key or definition.key
            element = data_context.values.get(source_key)
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
