from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..domain import BlockDefinition, DefinitionInput, ElementValue, ReportTemplate, SectionDefinition

SectionBuildMode = str
ElementMap = dict[str, ElementValue]


@dataclass(slots=True)
class SectionElementConfig(DefinitionInput):
    pass


@dataclass(slots=True)
class ReportSectionConfig:
    key: str
    title: str
    template: str | None = None
    block_mode: SectionBuildMode = "template_fill"
    prompt: str | None = None
    few_shots: list[dict[str, str]] = field(default_factory=list)
    elements: list[SectionElementConfig] = field(default_factory=list)
    children: list["ReportSectionConfig"] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    block_type: str = "rich_text"
    compute_key: str | None = None

    def to_section_definition(self) -> SectionDefinition:
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
            template=self.template,
            prompt_template=self.prompt,
            few_shots=list(self.few_shots),
            inputs=list(self.elements),
            compute_key=self.compute_key,
            options=dict(self.options),
        )
        return SectionDefinition(
            key=self.key,
            title=self.title,
            blocks=[block],
            children=[child.to_section_definition() for child in self.children],
            options=dict(self.options),
        )


@dataclass(slots=True)
class WordPipelineConfig:
    name: str = "fd-reportai-word"
    title: str = "Report"
    sections: list[ReportSectionConfig] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    version: str = "v1"

    def to_report_template(self) -> ReportTemplate:
        return ReportTemplate(
            key=self.name,
            version=self.version,
            title=self.title,
            sections=[section.to_section_definition() for section in self.sections],
            options=dict(self.options),
        )
