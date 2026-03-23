from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import WordContext


class BaseConverter(ABC):
    @abstractmethod
    def convert(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopConverter(BaseConverter):
    def convert(self, context: WordContext) -> None:
        for detection in context.detections:
            context.converted_blocks.append(
                {
                    "key": detection.get("key"),
                    "type": detection.get("type"),
                    "content": detection.get("payload"),
                }
            )
