from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import WordContext


class BaseValidator(ABC):
    @abstractmethod
    def validate(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopValidator(BaseValidator):
    def validate(self, context: WordContext) -> None:
        if context.framework is None:
            context.validation_errors.append("Framework config is missing.")

        if context.composed_document is None:
            context.validation_errors.append("Composed document is missing.")

        if context.blocked_items:
            context.validation_errors.append("Required elements are missing.")
        for result in context.block_results:
            if not result.validation.is_valid:
                for issue in result.validation.issues:
                    context.validation_errors.append(issue.message)
