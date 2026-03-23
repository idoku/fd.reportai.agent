from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


BlockType = str
GeneratorMode = str


@dataclass(slots=True)
class DefinitionInput:
    key: str
    source_key: str | None = None
    required: bool = True
    default_value: Any = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BlockDefinition:
    key: str
    title: str
    block_type: BlockType = "rich_text"
    generator_mode: GeneratorMode = "template"
    template: str | None = None
    compute_key: str | None = None
    prompt_template: str | None = None
    few_shots: list[dict[str, str]] = field(default_factory=list)
    inputs: list[DefinitionInput] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SectionDefinition:
    key: str
    title: str
    blocks: list[BlockDefinition] = field(default_factory=list)
    children: list["SectionDefinition"] = field(default_factory=list)
    enabled: bool = True
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReportTemplate:
    key: str
    version: str = "v1"
    title: str = "Report"
    sections: list[SectionDefinition] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GenerationPlan:
    template_key: str
    template_version: str
    sections: list[SectionDefinition] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
