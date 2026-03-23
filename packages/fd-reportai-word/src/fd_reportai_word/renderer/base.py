from __future__ import annotations

from abc import ABC, abstractmethod

from ..application import DefaultRenderer
from ..context import WordContext


class BaseRenderer(ABC):
    @abstractmethod
    def render(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopRenderer(BaseRenderer):
    def render(self, context: WordContext) -> None:
        if context.composed_document is None:
            context.rendered_output = None
            return
        context.rendered_output = DefaultRenderer().render(context.composed_document)
