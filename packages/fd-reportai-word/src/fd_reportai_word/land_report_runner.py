from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from .config import DEFAULT_PROMPTS_DIR, DEFAULT_TEMPLATES_DIR
from .land_blocks import LAND_BLOCKS, TemplateBlockConfig
from .llm import LLMLocator, SupportsInvoke


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(slots=True)
class BlockExecutionResult:
    block_key: str
    title: str
    selected_input: dict[str, Any]
    generated_fields: dict[str, Any]
    rendered_content: str
    prompt_preview: str
    provider: str
    model: str | None = None


@dataclass(slots=True)
class LandReportArtifacts:
    input_payload: dict[str, Any]
    block_results: list[BlockExecutionResult]
    markdown: str
    output_path: Path | None = None


class LandReportRunner:
    def __init__(
        self,
        *,
        locator: LLMLocator | None = None,
        llm: SupportsInvoke | None = None,
        prompts_dir: Path = DEFAULT_PROMPTS_DIR,
        templates_dir: Path = DEFAULT_TEMPLATES_DIR,
    ) -> None:
        self.locator = locator
        self.llm = llm
        self.prompts_dir = prompts_dir
        self.templates_dir = templates_dir

    def run_from_file(
        self,
        input_path: str | Path,
        *,
        block_keys: list[str] | None = None,
        output_path: str | Path | None = None,
    ) -> LandReportArtifacts:
        payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
        selected_keys = block_keys or ["cover"]

        block_results = [self._run_block(LAND_BLOCKS[key], payload) for key in selected_keys]
        markdown = self._assemble_markdown(block_results)

        destination: Path | None = None
        if output_path is not None:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(markdown, encoding="utf-8")

        return LandReportArtifacts(
            input_payload=payload,
            block_results=block_results,
            markdown=markdown,
            output_path=destination,
        )

    def _run_block(self, block: TemplateBlockConfig, payload: dict[str, Any]) -> BlockExecutionResult:
        selected_input = self._select_input(payload, block.input_keys)
        prompt = self._build_prompt(block, selected_input)
        llm = self._resolve_llm(block)
        if llm is None:
            raise RuntimeError(f"No LLM available for block {block.key}.")

        response = llm.invoke([HumanMessage(content=prompt)])
        content = self._extract_content(response)
        generated_fields = self._parse_json_object(content)
        missing = [field for field in block.output_fields if field not in generated_fields]
        if missing:
            raise ValueError(f"Block {block.key} missing generated fields: {missing}")

        rendered_content = self._render_template(block, generated_fields)
        provider = block.provider or (self.locator.provider if self.locator is not None else "custom")
        model = getattr(response, "response_metadata", {}).get("model_name")
        return BlockExecutionResult(
            block_key=block.key,
            title=block.title,
            selected_input=selected_input,
            generated_fields=generated_fields,
            rendered_content=rendered_content,
            prompt_preview=prompt[:400],
            provider=provider,
            model=model,
        )

    def _select_input(self, payload: dict[str, Any], input_keys: list[str]) -> dict[str, Any]:
        return {key: payload[key] for key in input_keys if key in payload}

    def _build_prompt(self, block: TemplateBlockConfig, selected_input: dict[str, Any]) -> str:
        if block.prompt_file is None:
            raise ValueError(f"Block {block.key} is missing prompt_file.")
        prompt_template = (self.prompts_dir / block.prompt_file).read_text(encoding="utf-8")
        return prompt_template.format_map(
            _SafeFormatDict(
                {
                    "输入数据JSON": json.dumps(selected_input, ensure_ascii=False, indent=2),
                    "输出字段JSON": json.dumps(block.output_fields, ensure_ascii=False),
                    "模板名称": block.template_file or "",
                    "区块标题": block.title,
                }
            )
        )

    def _resolve_llm(self, block: TemplateBlockConfig) -> SupportsInvoke | None:
        if self.locator is not None:
            block_locator = replace(
                self.locator,
                provider=block.provider or self.locator.provider,
                model=block.model or self.locator.model,
            )
            return block_locator.get_llm()
        return self.llm

    def _render_template(self, block: TemplateBlockConfig, fields: dict[str, Any]) -> str:
        if block.template_file is None:
            raise ValueError(f"Block {block.key} is missing template_file.")
        template = (self.templates_dir / block.template_file).read_text(encoding="utf-8")
        return template.format_map(_SafeFormatDict(fields)).strip()

    def _assemble_markdown(self, block_results: list[BlockExecutionResult]) -> str:
        parts = ["# 土地估价报告"]
        for block in block_results:
            parts.append(f"## {block.title}")
            parts.append(block.rendered_content)
        return "\n\n".join(part.strip() for part in parts if part and part.strip())

    def _extract_content(self, response: Any) -> str:
        content = getattr(response, "content", response)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
                else:
                    text = getattr(item, "text", None)
                    if text is not None:
                        parts.append(str(text))
            return "\n".join(part for part in parts if part).strip()
        return str(content)

    def _parse_json_object(self, text: str) -> dict[str, Any]:
        candidate = text.strip()
        if candidate.startswith("```"):
            candidate = candidate.split("\n", 1)[1]
            candidate = candidate.rsplit("```", 1)[0].strip()
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"LLM did not return a JSON object: {text}")
        return json.loads(candidate[start : end + 1])
