from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import WordContext


class BaseComposer(ABC):
    @abstractmethod
    def compose(self, context: WordContext) -> None:
        raise NotImplementedError


class NoopComposer(BaseComposer):
    def compose(self, context: WordContext) -> None:
        sections = self._compose_blocks(context.execution_blocks, context)

        context.section_outputs = sections
        context.composed_document = {
            "title": context.framework.title if context.framework else None,
            "sections": sections,
            "blocked_items": context.blocked_items,
        }

    def _compose_blocks(
        self,
        blocks: list[dict[str, object]],
        context: WordContext,
    ) -> list[dict[str, object]]:
        return [self._compose_block(block, context) for block in blocks]

    def _compose_block(
        self,
        block: dict[str, object],
        context: WordContext,
    ) -> dict[str, object]:
        children = self._compose_blocks(list(block.get("children", [])), context)
        content = self._render_block_content(block, context)

        return {
            "key": block["section_key"],
            "title": block["title"],
            "block_mode": block["block_mode"],
            "template": block.get("template"),
            "prompt": block.get("prompt"),
            "few_shots": block.get("few_shots", []),
            "elements": list(block.get("elements", [])),
            "missing_required_elements": list(block.get("missing_required_elements", [])),
            "content": content,
            "children": children,
            "options": dict(block.get("options", {})),
        }

    def _render_block_content(
        self,
        block: dict[str, object],
        context: WordContext,
    ) -> object:
        variables = {
            element["key"]: element.get("value")
            for element in block.get("elements", [])
            if element.get("value") is not None
        }
        mode = block["block_mode"]

        if mode == "template_fill":
            template = block.get("template")
            if isinstance(template, str):
                return template.format(**variables)
            return variables

        if mode == "prompt_generation":
            prompt_payload = self._build_prompt_payload(block, variables)
            prompt_generator = context.metadata.get("prompt_generator")
            if callable(prompt_generator):
                return prompt_generator(prompt_payload)
            return prompt_payload

        raise ValueError(f"Unsupported block mode: {mode}")

    def _build_prompt_payload(
        self,
        block: dict[str, object],
        variables: dict[str, object],
    ) -> dict[str, object]:
        prompt = block.get("prompt")
        formatted_prompt = prompt.format(**variables) if isinstance(prompt, str) else None
        return {
            "mode": "prompt_generation",
            "section_key": block["section_key"],
            "title": block["title"],
            "template": block.get("template"),
            "few_shots": list(block.get("few_shots", [])),
            "prompt": formatted_prompt,
            "variables": variables,
        }
