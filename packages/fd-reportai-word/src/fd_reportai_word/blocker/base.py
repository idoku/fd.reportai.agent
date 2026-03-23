from __future__ import annotations

from abc import ABC, abstractmethod

from ..application import DefaultBlocker
from ..context import WordContext
from ..domain import DataContext


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
