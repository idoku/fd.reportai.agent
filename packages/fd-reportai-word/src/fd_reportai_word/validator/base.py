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

        for block in context.execution_blocks:
            self._validate_block(block, context)

    def _validate_block(
        self,
        block: dict[str, object],
        context: WordContext,
    ) -> None:
        block_mode = block.get("block_mode")
        if block_mode not in {"template_fill", "prompt_generation"}:
            context.validation_errors.append(
                f"Unsupported block mode: {block_mode}."
            )

        if block_mode == "template_fill" and not block.get("template"):
            context.validation_errors.append(
                f"Section {block['section_key']} requires a template for template_fill mode."
            )

        if block_mode == "prompt_generation" and not block.get("prompt"):
            context.validation_errors.append(
                f"Section {block['section_key']} requires a prompt for prompt_generation mode."
            )

        for child in block.get("children", []):
            self._validate_block(child, context)
