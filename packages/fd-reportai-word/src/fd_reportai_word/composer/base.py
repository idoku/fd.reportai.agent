from __future__ import annotations

from abc import ABC, abstractmethod
import json

from langchain_core.messages import HumanMessage
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

from ..assembler import DefaultAssembler
from ..blocker.base import DefaultBlocker
from ..context import WordContext
from ..domain import (
    BlockResult,
    BlockTask,
    BlockTrace,
    ContentItemDefinition,
    ComputedFieldDefinition,
    DataContext,
    ValidationIssue,
    ValidationResult,
)
from ..domain.payloads import ElementValue
from ..llm import LLMLocator, SupportsInvoke
from ..transforms import apply_transform


class BaseComposer(ABC):
    @abstractmethod
    def compose(self, context: WordContext) -> None:
        raise NotImplementedError


class DefaultComposer:
    def __init__(
        self,
        *,
        locator: LLMLocator | None = None,
        llm: SupportsInvoke | None = None,
        computed_fields: dict[str, ComputedFieldDefinition] | None = None,
    ) -> None:
        self.locator = locator
        self.llm = llm
        self.computed_fields = dict(computed_fields or {})
        self.blocker = DefaultBlocker()

    def compose(self, task: BlockTask, data_context: DataContext) -> BlockResult:
        content = self._build_content(task, data_context)
        validation = self._validate(task, content)
        trace = BlockTrace(
            template_version=data_context.metadata.get("template_version"),
            rule_version=data_context.metadata.get("rule_version"),
            prompt_version=data_context.metadata.get("prompt_version"),
            model_version=data_context.metadata.get("model_version"),
            data_snapshot_id=data_context.snapshot_id,
            input_snapshot={item.key: item.value for item in task.resolved_inputs},
        )
        return BlockResult(
            section_key=task.section_key,
            block_key=task.definition.key,
            title=task.definition.title,
            block_type=task.definition.block_type,
            generator_mode=task.definition.generator_mode,
            content=content,
            resolved_inputs=task.resolved_inputs,
            missing_required_inputs=list(task.missing_required_inputs),
            trace=trace,
            validation=validation,
            options=dict(task.options),
        )

    def _build_content(self, task: BlockTask, data_context: DataContext):
        self._resolve_computed_inputs(task, data_context)
        variables = {resolved.key: resolved.value for resolved in task.resolved_inputs if resolved.has_value}
        variables.update(self._build_content_item_values(task.definition.content_items, data_context))
        mode = task.definition.generator_mode
        block_type = task.definition.block_type

        if mode == "template":
            template = task.definition.template or ""
            rendered = template.format_map(_SafeFormatDict(variables))
            return self._shape_content(block_type, rendered)

        if mode == "computed":
            compute_registry = data_context.metadata.get("compute_registry", {})
            compute_fn = compute_registry.get(task.definition.compute_key or task.definition.key)
            if not callable(compute_fn):
                raise ValueError(f"Missing compute function for block {task.definition.key}.")
            computed = compute_fn(variables, task=task)
            return self._shape_content(block_type, computed)

        if mode == "ai":
            prompt = self._build_ai_prompt(task, variables)
            llm = self._resolve_llm()
            if llm is None:
                return {
                    "type": block_type,
                    "generator_mode": "ai",
                    "mode": "prompt_generation",
                    "prompt": prompt,
                    "few_shots": list(task.definition.few_shots),
                    "variables": variables,
                }

            response = llm.invoke([HumanMessage(content=prompt)])
            response_text = self._extract_content(response)
            data_context.metadata["model_version"] = self._extract_model_name(response)
            generated_fields = self._parse_json_object(response_text)
            if task.definition.template:
                rendered = task.definition.template.format_map(_SafeFormatDict(generated_fields))
                return self._shape_content(block_type, rendered)
            return {
                "type": block_type,
                "generator_mode": "ai",
                "mode": "llm_result",
                "prompt": prompt,
                "response": response_text,
                "fields": generated_fields,
                "few_shots": list(task.definition.few_shots),
                "variables": variables,
            }

        raise ValueError(f"Unsupported generator mode: {mode}.")

    def _shape_content(self, block_type: str, raw_content):
        if block_type == "rich_text":
            return {"type": "rich_text", "text": raw_content if isinstance(raw_content, str) else str(raw_content)}
        if block_type == "table":
            if isinstance(raw_content, dict):
                return {"type": "table", **raw_content}
            return {"type": "table", "rows": raw_content}
        if block_type == "image_group":
            if isinstance(raw_content, dict):
                return {"type": "image_group", **raw_content}
            return {"type": "image_group", "items": raw_content}
        return {"type": block_type, "content": raw_content}

    def _validate(self, task: BlockTask, content) -> ValidationResult:
        issues: list[ValidationIssue] = []
        if task.missing_required_inputs:
            issues.append(
                ValidationIssue(
                    code="missing_required_inputs",
                    message=f"Block {task.definition.key} is missing required inputs.",
                )
            )
        if task.definition.generator_mode == "template" and not task.definition.template:
            issues.append(
                ValidationIssue(
                    code="missing_template",
                    message=f"Block {task.definition.key} requires a template.",
                )
            )
        if task.definition.generator_mode == "ai" and not task.definition.prompt_template:
            issues.append(
                ValidationIssue(
                    code="missing_prompt_template",
                    message=f"Block {task.definition.key} requires a prompt template.",
                )
            )
        if isinstance(content, dict) and not content:
            issues.append(
                ValidationIssue(
                    code="empty_content",
                    message=f"Block {task.definition.key} produced empty content.",
                )
            )
        return ValidationResult(is_valid=not issues, issues=issues)

    def _build_ai_prompt(self, task: BlockTask, variables: dict[str, object]) -> str:
        return self._render_prompt_template(
            prompt_template=task.definition.prompt_template or "",
            prompt_variables={
                "input": json.dumps(variables, ensure_ascii=False, indent=2),
            },
            few_shots=task.definition.few_shots,
        )

    def _build_content_item_values(
        self,
        content_items: list[ContentItemDefinition],
        data_context: DataContext,
    ) -> dict[str, str]:
        values: dict[str, str] = {}
        for content_item in content_items:
            values[content_item.key] = self._render_content_item(content_item, data_context)
        return values

    def _render_content_item(
        self,
        content_item: ContentItemDefinition,
        data_context: DataContext,
    ) -> str:
        variables = self._resolve_content_item_variables(content_item.inputs, data_context)
        if content_item.prompt_template:
            prompt = self._render_prompt_template(
                prompt_template=content_item.prompt_template,
                prompt_variables={
                    "input": json.dumps(variables, ensure_ascii=False, indent=2),
                },
                few_shots=content_item.few_shots,
            )
            llm = self._resolve_llm()
            if llm is None:
                return prompt
            response = llm.invoke([HumanMessage(content=prompt)])
            response_text = self._extract_content(response)
            if data_context.metadata.get("model_version") is None:
                data_context.metadata["model_version"] = self._extract_model_name(response)
            if content_item.template:
                generated_fields = self._parse_json_object(response_text)
                return content_item.template.format_map(_SafeFormatDict(generated_fields))
            return self._strip_text_result(response_text)
        template = content_item.template or ""
        return template.format_map(_SafeFormatDict(variables))

    def _resolve_content_item_variables(
        self,
        definitions: list,
        data_context: DataContext,
    ) -> dict[str, object]:
        resolved_inputs = self.blocker._resolve_inputs(definitions, data_context)
        self._resolve_computed_values(resolved_inputs, data_context)
        return {resolved.key: resolved.value for resolved in resolved_inputs if resolved.has_value}

    def _resolve_computed_inputs(self, task: BlockTask, data_context: DataContext) -> None:
        self._resolve_computed_values(task.resolved_inputs, data_context)
        task.missing_required_inputs = [
            resolved.key for resolved in task.resolved_inputs if resolved.required and not resolved.has_value
        ]

    def _resolve_computed_values(self, resolved_inputs, data_context: DataContext) -> None:
        for resolved in resolved_inputs:
            if resolved.has_value:
                continue
            existing_value = data_context.values.get(resolved.source_key)
            if existing_value is not None:
                resolved.value = existing_value.value
                resolved.has_value = True
                resolved.used_default = False
                continue
            computed_field = self.computed_fields.get(resolved.source_key)
            if computed_field is not None:
                value = self._get_or_compute_field_value(computed_field, data_context)
                if value is None:
                    continue
                resolved.value = value
                resolved.has_value = True
                resolved.used_default = False
                continue
            if self._resolve_from_json_computed_fields(resolved, data_context):
                continue

    def _get_or_compute_field_value(
        self,
        computed_field: ComputedFieldDefinition,
        data_context: DataContext,
    ) -> object | None:
        existing = data_context.values.get(computed_field.key)
        if existing is not None:
            return existing.value
        value = self._compute_field_value(computed_field, data_context)
        if value is None:
            return None
        self._store_computed_field_value(computed_field, value, data_context)
        return value

    def _store_computed_field_value(
        self,
        computed_field: ComputedFieldDefinition,
        value: object,
        data_context: DataContext,
    ) -> None:
        element_options = {
            "computed": True,
            "mode": computed_field.mode,
        }
        data_context.values[computed_field.key] = ElementValue(
            value=value,
            options=dict(element_options),
        )
        if not isinstance(value, dict):
            return
        for child_key, child_value in value.items():
            if child_key in data_context.values:
                continue
            child_options = dict(element_options)
            child_options["computed_parent"] = computed_field.key
            data_context.values[child_key] = ElementValue(
                value=child_value,
                options=child_options,
            )

    def _resolve_from_json_computed_fields(self, resolved, data_context: DataContext) -> bool:
        value = self._find_resolved_value(resolved, data_context)
        if value is not None:
            resolved.value = value
            resolved.has_value = True
            resolved.used_default = False
            return True

        for computed_field in self.computed_fields.values():
            if computed_field.mode != "llm_json":
                continue
            value = self._get_or_compute_field_value(computed_field, data_context)
            if value is None:
                continue
            matched_value = self._find_resolved_value(resolved, data_context)
            if matched_value is None:
                continue
            resolved.value = matched_value
            resolved.has_value = True
            resolved.used_default = False
            return True
        return False

    def _find_resolved_value(self, resolved, data_context: DataContext) -> object | None:
        existing = data_context.values.get(resolved.source_key)
        transform = resolved.options.get("transform")
        if existing is not None:
            if transform is None:
                return existing.value
            return self._apply_transform(existing.value, transform, data_context)
        nested = self.blocker._find_nested_value(data_context.values, resolved.source_key)
        if nested is None:
            return None
        if transform is None:
            return nested
        return self._apply_transform(nested, transform, data_context)

    def _compute_field_value(
        self,
        computed_field: ComputedFieldDefinition,
        data_context: DataContext,
    ) -> object | None:
        if computed_field.mode == "fixed":
            return computed_field.options.get("value")

        if computed_field.mode == "extract":
            path = computed_field.options.get("path")
            if not isinstance(path, str) or not path.strip():
                raise ValueError(f"Computed field {computed_field.key} requires options['path'] for extract mode.")
            value = self._extract_from_path(data_context, path)
            transform = computed_field.options.get("transform")
            if transform is not None:
                value = self._apply_transform(value, transform, data_context)
            return value

        if computed_field.mode not in {"llm_text", "llm_json", "llm_table"}:
            raise ValueError(f"Unsupported computed field mode: {computed_field.mode}.")

        llm = self._resolve_llm()
        if llm is None:
            return None

        prompt_template = computed_field.prompt_template or ""
        if computed_field.input_blocks:
            variables = self._get_computed_field_input_blocks(computed_field, data_context)
        else:
            variables = {key: element.value for key, element in data_context.values.items()}
        prompt = self._render_prompt_template(
            prompt_template=prompt_template,
            prompt_variables={
                "input": json.dumps(variables, ensure_ascii=False, indent=2),
                "template": computed_field.template or "",
            },
            few_shots=computed_field.few_shots,
        )
        invoke_kwargs: dict[str, object] = {}
        max_tokens = computed_field.options.get("max_tokens")
        if isinstance(max_tokens, int) and max_tokens > 0:
            invoke_kwargs["max_tokens"] = max_tokens
        response = llm.invoke([HumanMessage(content=prompt)], **invoke_kwargs)
        response_text = self._extract_content(response)
        if data_context.metadata.get("model_version") is None:
            data_context.metadata["model_version"] = self._extract_model_name(response)
        if computed_field.mode == "llm_json":
            return self._parse_json_object(response_text)
        return self._strip_text_result(response_text)

    def _extract_from_path(self, data_context: DataContext, path: str) -> object | None:
        current: object | None = data_context.values
        for part in path.split("."):
            if current is None:
                return None
            current = self._resolve_path_part(current, part)
        if isinstance(current, ElementValue):
            return current.value
        return current

    def _resolve_path_part(self, current: object, part: str) -> object | None:
        token = part.strip()
        if not token:
            return current

        while token:
            if "[" in token:
                field_name, rest = token.split("[", 1)
                if field_name:
                    current = self._resolve_mapping_value(current, field_name)
                index_text, remainder = rest.split("]", 1)
                if not isinstance(current, list):
                    return None
                try:
                    current = current[int(index_text)]
                except (ValueError, IndexError):
                    return None
                token = remainder
            else:
                current = self._resolve_mapping_value(current, token)
                token = ""
        return current

    def _resolve_mapping_value(self, current: object, key: str) -> object | None:
        if isinstance(current, ElementValue):
            current = current.value
        if isinstance(current, dict):
            return current.get(key)
        return None

    def _apply_transform(self, value: object | None, transform: object, data_context: DataContext) -> object | None:
        return apply_transform(value, transform, data_context.metadata)

    def _find_element_for_definition(
        self,
        definition,
        data_context: DataContext,
    ) -> tuple[str, ElementValue | None]:
        candidate_keys = [definition.source_key or definition.key, *definition.aliases]
        for candidate_key in candidate_keys:
            element = data_context.values.get(candidate_key)
            if element is not None:
                return candidate_key, element
        return definition.source_key or definition.key, None

    def _get_computed_field_input_blocks(
        self,
        computed_field: ComputedFieldDefinition,
        data_context: DataContext,
    ) -> dict[str, object]:
        variables: dict[str, object] = {}
        for input_definition in computed_field.input_blocks:
            _, element = self._find_element_for_definition(input_definition, data_context)
            if element is not None:
                variables[input_definition.key] = element.value
            elif input_definition.default_value is not None:
                variables[input_definition.key] = input_definition.default_value
        return variables

    def _strip_text_result(self, text: str) -> str:
        candidate = text.strip()
        if candidate.startswith("```"):
            candidate = candidate.split("\n", 1)[1]
            candidate = candidate.rsplit("```", 1)[0].strip()
        return candidate.strip().strip('"').strip("'")

    def _render_prompt_template(
        self,
        *,
        prompt_template: str,
        prompt_variables: dict[str, object],
        few_shots: list[dict[str, str]] | None = None,
    ) -> str:
        if "{examples}" not in prompt_template:
            return prompt_template.format_map(_SafeFormatDict(prompt_variables))

        prefix, suffix = prompt_template.split("{examples}", 1)
        examples = [
            {"example": self._serialize_few_shot_example(example)}
            for example in (few_shots or [])
        ]
        few_shot_prompt = FewShotPromptTemplate(
            examples=examples,
            example_prompt=PromptTemplate.from_template("{example}"),
            prefix=prefix.rstrip(),
            suffix=suffix.lstrip(),
            input_variables=list(prompt_variables.keys()),
            example_separator="\n\n",
        )
        return few_shot_prompt.format(**prompt_variables)

    def _serialize_few_shot_example(self, example: dict[str, object]) -> str:
        normalized = {
            key: self._coerce_example_value(value, key=key)
            for key, value in example.items()
        }
        if "input_data" in normalized or "standard_output" in normalized:
            parts: list[str] = []
            if "input_data" in normalized:
                parts.append("【示例输入】")
                parts.append(normalized["input_data"].strip())
            if "standard_output" in normalized:
                parts.append("【标准输出】")
                parts.append(normalized["standard_output"].strip())
            for key, value in normalized.items():
                if key in {"input_data", "standard_output"}:
                    continue
                parts.append(f"【{key}】")
                parts.append(value.strip())
            return "\n".join(part for part in parts if part).strip()

        lines: list[str] = []
        for key, value in normalized.items():
            lines.append(f"{key}:")
            lines.append(value)
        return "\n".join(lines).strip()

    def _coerce_example_value(self, value: object, *, key: str) -> str:
        if isinstance(value, list):
            separator = "\n\n" if key == "output" else "\n"
            return separator.join(str(item).rstrip() for item in value).strip()
        if isinstance(value, str):
            return value
        return str(value)

    def _resolve_llm(self) -> SupportsInvoke | None:
        if self.locator is not None:
            return self.locator.get_llm()
        return self.llm

    def _extract_content(self, response) -> str:
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

    def _extract_model_name(self, response) -> str | None:
        metadata = getattr(response, "response_metadata", {})
        if isinstance(metadata, dict):
            return metadata.get("model_name")
        return None

    def _parse_json_object(self, text: str) -> dict[str, object]:
        candidate = text.strip()
        if candidate.startswith("```"):
            candidate = candidate.split("\n", 1)[1]
            candidate = candidate.rsplit("```", 1)[0].strip()
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"LLM did not return a JSON object: {text}")
        return json.loads(candidate[start : end + 1])


class NoopComposer(BaseComposer):
    def __init__(
        self,
        *,
        locator: LLMLocator | None = None,
        llm: SupportsInvoke | None = None,
    ) -> None:
        self.locator = locator
        self.llm = llm

    def compose(self, context: WordContext) -> None:
        if context.framework is None or context.plan is None or context.data_context is None:
            context.composed_document = None
            context.block_results = []
            return

        computed_fields = {
            field_definition.key: field_definition for field_definition in context.template.computed_fields
        }
        composer = DefaultComposer(
            locator=self.locator,
            llm=self.llm,
            computed_fields=computed_fields,
        )
        block_results = {}
        flat_results = []
        for section in self._walk_sections(context.planned_sections):
            for task in section.tasks:
                result = composer.compose(task, context.data_context)
                block_results[(task.section_key, task.definition.key)] = result
                flat_results.append(result)

        context.block_results = flat_results
        context.composed_document = DefaultAssembler().assemble(
            title=context.framework.title,
            template_key=context.plan.template_key,
            template_version=context.plan.template_version,
            sections=context.planned_sections,
            block_results=block_results,
            blocked_items=list(context.blocked_items),
            metadata=dict(context.metadata),
        )

    def _walk_sections(self, sections):
        for section in sections:
            yield section
            yield from self._walk_sections(section.children)


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
