from __future__ import annotations

from abc import ABC, abstractmethod

from ..application import DefaultAssembler, DefaultComposer
from ..context import WordContext


class BaseComposer(ABC):
    @abstractmethod
    def compose(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopComposer(BaseComposer):
    def compose(self, context: WordContext) -> None:
        if context.framework is None or context.plan is None or context.data_context is None:
            context.composed_document = None
            context.block_results = []
            return

        composer = DefaultComposer()
        block_results = {}
        flat_results = []
        for section in self._walk_sections(context.planned_sections):
            for task in section.tasks:
                result = composer.compose(task, context.data_context)
                block_results[(task.section_key, task.definition.key)] = result
                flat_results.append(result)

        context.block_results = flat_results
        context.composed_document = DefaultAssembler().assemble(
            title=context.framework.title,
            template_key=context.plan.template_key,
            template_version=context.plan.template_version,
            sections=context.planned_sections,
            block_results=block_results,
            blocked_items=list(context.blocked_items),
            metadata=dict(context.metadata),
        )

    def _walk_sections(self, sections):
        for section in sections:
            yield section
            yield from self._walk_sections(section.children)
