from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import WordContext


class BaseRenderer(ABC):
    @abstractmethod
    def render(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopRenderer(BaseRenderer):
    def render(self, context: WordContext) -> None:
        context.rendered_output = context.composed_document
