from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

from ..domain import (
    BlockDefinition,
    ContentItemDefinition,
    ComputedFieldDefinition,
    DefinitionInput,
    ElementValue,
    ReportTemplate,
    SectionDefinition,
)

SectionBuildMode = str
ElementMap = dict[str, ElementValue]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES_DIR = PACKAGE_ROOT / "rules"
DEFAULT_TEMPLATES_DIR = PACKAGE_ROOT / "templates"
DEFAULT_PROMPTS_DIR = PACKAGE_ROOT / "prompts"
_INCLUDE_PATTERN = re.compile(r"\{\{\s*include\s*:\s*([^}]+?)\s*\}\}")


@dataclass(slots=True)
class SectionElementConfig(DefinitionInput):
    pass


@dataclass(slots=True)
class ContentItemConfig:
    key: str
    template: str | None = None
    template_file: str | None = None
    prompt: str | None = None
    prompt_file: str | None = None
    elements: list[SectionElementConfig] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)

    def to_definition(
        self,
        *,
        templates_dir: Path | None = None,
        prompts_dir: Path | None = None,
    ) -> ContentItemDefinition:
        return ContentItemDefinition(
            key=self.key,
            template=self._resolve_template(templates_dir),
            prompt_template=self._resolve_prompt(prompts_dir),
            inputs=list(self.elements),
            options=dict(self.options),
        )

    def _resolve_template(self, templates_dir: Path | None) -> str | None:
        if self.template is not None:
            return self.template
        if self.template_file is None:
            return None
        if templates_dir is None:
            raise ValueError(f"templates_dir is required for template_file={self.template_file!r}.")
        return _load_text_with_includes(
            base_dir=templates_dir,
            relative_path=self.template_file,
        )

    def _resolve_prompt(self, prompts_dir: Path | None) -> str | None:
        if self.prompt is not None:
            return self.prompt
        if self.prompt_file is None:
            return None
        if prompts_dir is None:
            raise ValueError(f"prompts_dir is required for prompt_file={self.prompt_file!r}.")
        return _load_text_with_includes(
            base_dir=prompts_dir,
            relative_path=self.prompt_file,
        )


@dataclass(slots=True)
class ComputedFieldConfig:
    key: str
    mode: str
    prompt: str | None = None
    prompt_file: str | None = None
    template: str | None = None
    template_file: str | None = None
    input_blocks: list[SectionElementConfig] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)

    def to_definition(
        self,
        *,
        prompts_dir: Path | None = None,
        templates_dir: Path | None = None,
    ) -> ComputedFieldDefinition:
        return ComputedFieldDefinition(
            key=self.key,
            mode=self.mode,
            prompt_template=self._resolve_prompt(prompts_dir),
            template=self._resolve_template(templates_dir),
            input_blocks=list(self.input_blocks),
            options=dict(self.options),
        )

    def _resolve_prompt(self, prompts_dir: Path | None) -> str | None:
        if self.prompt is not None:
            return self.prompt
        if self.prompt_file is None:
            return None
        if prompts_dir is None:
            raise ValueError(f"prompts_dir is required for prompt_file={self.prompt_file!r}.")
        return _load_text_with_includes(
            base_dir=prompts_dir,
            relative_path=self.prompt_file,
        )

    def _resolve_template(self, templates_dir: Path | None) -> str | None:
        if self.template is not None:
            return self.template
        if self.template_file is None:
            return None
        if templates_dir is None:
            raise ValueError(f"templates_dir is required for template_file={self.template_file!r}.")
        return _load_text_with_includes(
            base_dir=templates_dir,
            relative_path=self.template_file,
        )


@dataclass(slots=True)
class ReportSectionConfig:
    key: str
    title: str
    template: str | None = None
    template_file: str | None = None
    block_mode: SectionBuildMode = "template_fill"
    prompt: str | None = None
    prompt_file: str | None = None
    few_shots: list[dict[str, str]] = field(default_factory=list)
    elements: list[SectionElementConfig] = field(default_factory=list)
    content_items: list[ContentItemConfig] = field(default_factory=list)
    children: list["ReportSectionConfig"] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    block_type: str = "rich_text"
    compute_key: str | None = None

    def to_section_definition(
        self,
        *,
        templates_dir: Path | None = None,
        prompts_dir: Path | None = None,
    ) -> SectionDefinition:
        generator_mode = {
            "template_fill": "template",
            "prompt_generation": "ai",
            "computed": "computed",
        }.get(self.block_mode, self.block_mode)
        block = BlockDefinition(
            key=self.key,
            title=self.title,
            block_type=self.block_type,
            generator_mode=generator_mode,
            template=self._resolve_template(templates_dir),
            prompt_template=self._resolve_prompt(prompts_dir),
            few_shots=list(self.few_shots),
            inputs=list(self.elements),
            content_items=[
                content_item.to_definition(templates_dir=templates_dir, prompts_dir=prompts_dir)
                for content_item in self.content_items
            ],
            compute_key=self.compute_key,
            options=dict(self.options),
        )
        return SectionDefinition(
            key=self.key,
            title=self.title,
            blocks=[block],
            children=[
                child.to_section_definition(templates_dir=templates_dir, prompts_dir=prompts_dir)
                for child in self.children
            ],
            options=dict(self.options),
        )

    def _resolve_template(self, templates_dir: Path | None) -> str | None:
        if self.template is not None:
            return self.template
        if self.template_file is None:
            return None
        if templates_dir is None:
            raise ValueError(f"templates_dir is required for template_file={self.template_file!r}.")
        return _load_text_with_includes(
            base_dir=templates_dir,
            relative_path=self.template_file,
        )

    def _resolve_prompt(self, prompts_dir: Path | None) -> str | None:
        if self.prompt is not None:
            return self.prompt
        if self.prompt_file is None:
            return None
        if prompts_dir is None:
            raise ValueError(f"prompts_dir is required for prompt_file={self.prompt_file!r}.")
        return _load_text_with_includes(
            base_dir=prompts_dir,
            relative_path=self.prompt_file,
        )


@dataclass(slots=True)
class WordPipelineConfig:
    name: str = "fd-reportai-word"
    title: str = "Report"
    computed_fields: list[ComputedFieldConfig] = field(default_factory=list)
    sections: list[ReportSectionConfig] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    version: str = "v1"
    rules_dir: str | Path | None = DEFAULT_RULES_DIR
    templates_dir: str | Path | None = None
    prompts_dir: str | Path | None = None

    def to_report_template(self) -> ReportTemplate:
        templates_dir = (
            Path(self.templates_dir) if self.templates_dir is not None else DEFAULT_TEMPLATES_DIR
        )
        prompts_dir = (
            Path(self.prompts_dir) if self.prompts_dir is not None else DEFAULT_PROMPTS_DIR
        )
        return ReportTemplate(
            key=self.name,
            version=self.version,
            title=self.title,
            computed_fields=[
                field_config.to_definition(prompts_dir=prompts_dir, templates_dir=templates_dir)
                for field_config in self.computed_fields
            ],
            sections=[
                section.to_section_definition(templates_dir=templates_dir, prompts_dir=prompts_dir)
                for section in self.sections
            ],
            options=dict(self.options),
        )


def _load_text_with_includes(
    *,
    base_dir: Path,
    relative_path: str,
    visited: tuple[Path, ...] = (),
) -> str:
    file_path = (base_dir / relative_path).resolve()
    if file_path in visited:
        cycle = " -> ".join(str(path) for path in (*visited, file_path))
        raise ValueError(f"Template include cycle detected: {cycle}")

    content = file_path.read_text(encoding="utf-8")

    def replace_include(match: re.Match[str]) -> str:
        include_ref = match.group(1).strip()
        include_path = file_path.parent / include_ref
        return _load_text_with_includes(
            base_dir=include_path.parent,
            relative_path=include_path.name,
            visited=(*visited, file_path),
        )

    return _INCLUDE_PATTERN.sub(replace_include, content)
