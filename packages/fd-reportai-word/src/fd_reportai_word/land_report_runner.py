from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from .config import DEFAULT_PROMPTS_DIR, ElementValue
from .context import WordContext
from .converters import LandValuationCoverConverter
from .llm import LLMLocator, SupportsInvoke
from .pipeline import WordPipeline


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(slots=True)
class PromptTask:
    target_key: str
    prompt_file: str | None = None
    prompt_template: str | None = None
    provider: str | None = None
    model: str | None = None
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class PromptFieldGenerator:
    def __init__(
        self,
        *,
        prompts_dir: Path = DEFAULT_PROMPTS_DIR,
        locator: LLMLocator | None = None,
        llm: SupportsInvoke | None = None,
    ) -> None:
        self.prompts_dir = prompts_dir
        self.locator = locator
        self.llm = llm

    def generate(
        self,
        tasks: list[PromptTask],
        variables: dict[str, Any],
    ) -> tuple[dict[str, str], list[dict[str, Any]]]:
        generated: dict[str, str] = {}
        traces: list[dict[str, Any]] = []

        for task in tasks:
            if not task.enabled:
                continue

            prompt_template = self._load_prompt_template(task)
            rendered_prompt = prompt_template.format_map(_SafeFormatDict(variables))
            llm = self._resolve_llm(task)
            if llm is None:
                raise RuntimeError("LLM client is required for enabled prompt tasks.")

            response = llm.invoke(
                [HumanMessage(content=rendered_prompt)],
                metadata={"target_key": task.target_key, **task.metadata},
            )
            content = self._extract_content(response)
            generated[task.target_key] = content
            variables[task.target_key] = content
            traces.append(
                {
                    "target_key": task.target_key,
                    "model": getattr(response, "response_metadata", {}).get("model_name", task.model),
                    "prompt_preview": rendered_prompt[:400],
                }
            )

        return generated, traces

    def _load_prompt_template(self, task: PromptTask) -> str:
        if task.prompt_template is not None:
            return task.prompt_template
        if task.prompt_file is None:
            raise ValueError(f"Prompt task {task.target_key} requires prompt_file or prompt_template.")
        return (self.prompts_dir / task.prompt_file).read_text(encoding="utf-8")

    def _resolve_llm(self, task: PromptTask) -> SupportsInvoke | None:
        if self.locator is not None:
            task_locator = replace(
                self.locator,
                provider=task.provider or self.locator.provider,
                model=task.model or self.locator.model,
            )
            return task_locator.get_llm()
        return self.llm

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


@dataclass(slots=True)
class LandReportArtifacts:
    input_payload: dict[str, Any]
    generated_fields: dict[str, str]
    prompt_traces: list[dict[str, Any]]
    context: WordContext
    output_path: Path | None = None


class LandReportRunner:
    def __init__(
        self,
        *,
        locator: LLMLocator | None = None,
        llm: SupportsInvoke | None = None,
    ) -> None:
        self.locator = locator
        self.llm = llm
        self.pipeline = WordPipeline(converters=[LandValuationCoverConverter()])

    def run_from_file(
        self,
        input_path: str | Path,
        *,
        output_path: str | Path | None = None,
    ) -> LandReportArtifacts:
        input_file = Path(input_path)
        payload = json.loads(input_file.read_text(encoding="utf-8"))

        cover_inputs = dict(payload.get("封面", {}))
        summary_inputs = dict(payload.get("摘要", {}))
        shared_inputs = dict(payload.get("共享输入", {}))

        merged_variables = {**shared_inputs, **cover_inputs, **summary_inputs}
        prompt_tasks = [
            PromptTask(
                target_key=str(item["目标字段"]),
                prompt_file=item.get("提示词文件"),
                prompt_template=item.get("提示词模板"),
                provider=item.get("提供方"),
                model=item.get("模型"),
                enabled=bool(item.get("启用", True)),
                metadata={"task_name": item.get("任务名称", item.get("目标字段", ""))},
            )
            for item in payload.get("提示词任务", [])
        ]

        generated_fields, prompt_traces = PromptFieldGenerator(
            locator=self.locator,
            llm=self.llm,
        ).generate(prompt_tasks, merged_variables)
        summary_inputs.update(generated_fields)

        context = WordContext(
            metadata={
                "data_snapshot_id": str(payload.get("数据快照ID", input_file.stem)),
                "prompt_traces": prompt_traces,
            },
            elements={
                key: ElementValue(value=value)
                for key, value in {**shared_inputs, **summary_inputs}.items()
            },
            detections=[
                {
                    "key": "land_valuation_cover",
                    "payload": cover_inputs,
                }
            ],
        )
        result = self.pipeline.run(context=context)

        destination: Path | None = None
        if output_path is not None:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(result.rendered_output["markdown"], encoding="utf-8")

        return LandReportArtifacts(
            input_payload=payload,
            generated_fields=generated_fields,
            prompt_traces=prompt_traces,
            context=result,
            output_path=destination,
        )
