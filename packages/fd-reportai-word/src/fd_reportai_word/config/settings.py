from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SectionBuildMode = str
ElementMap = dict[str, "ElementValue"]


@dataclass(slots=True)
class ElementValue:
    value: Any
    label: str | None = None
    type: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SectionElementConfig:
    key: str
    required: bool = True
    source_key: str | None = None
    default_value: Any = None
    options: dict[str, Any] = field(default_factory=dict)


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


@dataclass(slots=True)
class WordPipelineConfig:
    name: str = "fd-reportai-word"
    title: str = "Report"
    sections: list[ReportSectionConfig] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
