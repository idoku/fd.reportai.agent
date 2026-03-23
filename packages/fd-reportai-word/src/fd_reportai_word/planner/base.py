from __future__ import annotations

from abc import ABC, abstractmethod

from ..application import DefaultPlanner
from ..context import WordContext


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
