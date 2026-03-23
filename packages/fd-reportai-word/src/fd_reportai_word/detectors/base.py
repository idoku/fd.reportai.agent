from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import WordContext


class BaseDetector(ABC):
    @abstractmethod
    def detect(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopDetector(BaseDetector):
    def detect(self, context: WordContext) -> None:
        for key, value in context.elements.items():
            context.detections.append(
                {
                    "type": "element",
                    "key": key,
                    "payload": value.value,
                    "element": value,
                }
            )
