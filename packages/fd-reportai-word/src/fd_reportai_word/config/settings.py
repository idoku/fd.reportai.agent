from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..domain import BlockDefinition, DefinitionInput, ElementValue, ReportTemplate, SectionDefinition

SectionBuildMode = str
ElementMap = dict[str, ElementValue]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES_DIR = PACKAGE_ROOT / "rules" / "default"


@dataclass(slots=True)
class SectionElementConfig(DefinitionInput):
    pass


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
    children: list["ReportSectionConfig"] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    block_type: str = "rich_text"
    compute_key: str | None = None

    def to_section_definition(
        self,
        *,
        markdown_dir: Path | None = None,
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
            template=self._resolve_template(markdown_dir),
            prompt_template=self._resolve_prompt(prompts_dir),
            few_shots=list(self.few_shots),
            inputs=list(self.elements),
            compute_key=self.compute_key,
            options=dict(self.options),
        )
        return SectionDefinition(
            key=self.key,
            title=self.title,
            blocks=[block],
            children=[
                child.to_section_definition(markdown_dir=markdown_dir, prompts_dir=prompts_dir)
                for child in self.children
            ],
            options=dict(self.options),
        )

    def _resolve_template(self, markdown_dir: Path | None) -> str | None:
        if self.template is not None:
            return self.template
        if self.template_file is None:
            return None
        if markdown_dir is None:
            raise ValueError(f"markdown_dir is required for template_file={self.template_file!r}.")
        return (markdown_dir / self.template_file).read_text(encoding="utf-8")

    def _resolve_prompt(self, prompts_dir: Path | None) -> str | None:
        if self.prompt is not None:
            return self.prompt
        if self.prompt_file is None:
            return None
        if prompts_dir is None:
            raise ValueError(f"prompts_dir is required for prompt_file={self.prompt_file!r}.")
        return (prompts_dir / self.prompt_file).read_text(encoding="utf-8")


@dataclass(slots=True)
class WordPipelineConfig:
    name: str = "fd-reportai-word"
    title: str = "Report"
    sections: list[ReportSectionConfig] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    version: str = "v1"
    rules_dir: str | Path | None = DEFAULT_RULES_DIR
    markdown_dir: str | Path | None = None
    prompts_dir: str | Path | None = None

    def to_report_template(self) -> ReportTemplate:
        rules_dir = Path(self.rules_dir) if self.rules_dir is not None else None
        markdown_dir = Path(self.markdown_dir) if self.markdown_dir is not None else (
            rules_dir / "markdown" if rules_dir is not None else None
        )
        prompts_dir = Path(self.prompts_dir) if self.prompts_dir is not None else (
            rules_dir / "prompts" if rules_dir is not None else None
        )
        return ReportTemplate(
            key=self.name,
            version=self.version,
            title=self.title,
            sections=[
                section.to_section_definition(markdown_dir=markdown_dir, prompts_dir=prompts_dir)
                for section in self.sections
            ],
            options=dict(self.options),
        )
