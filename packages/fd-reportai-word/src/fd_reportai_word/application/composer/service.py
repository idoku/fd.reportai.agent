from __future__ import annotations

from typing import Any

from ...domain import BlockResult, BlockTask, BlockTrace, DataContext, ValidationIssue, ValidationResult


class DefaultComposer:
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

    def _build_content(self, task: BlockTask, data_context: DataContext) -> Any:
        variables = {resolved.key: resolved.value for resolved in task.resolved_inputs if resolved.has_value}
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
            prompt = (task.definition.prompt_template or "").format_map(_SafeFormatDict(variables))
            return {
                "type": block_type,
                "generator_mode": "ai",
                "mode": "prompt_generation",
                "prompt": prompt,
                "few_shots": list(task.definition.few_shots),
                "variables": variables,
            }

        raise ValueError(f"Unsupported generator mode: {mode}.")

    def _shape_content(self, block_type: str, raw_content: Any) -> Any:
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

    def _validate(self, task: BlockTask, content: Any) -> ValidationResult:
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


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
