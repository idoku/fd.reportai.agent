from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import ElementMap, WordPipelineConfig
from .domain import BlockResult, DataContext, GenerationPlan, PlannedSection, ReportDocument, ReportTemplate


@dataclass(slots=True)
class WordContext:
    framework: WordPipelineConfig | None = None
    elements: ElementMap = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    template: ReportTemplate | None = None
    data_context: DataContext | None = None
    detections: list[dict[str, Any]] = field(default_factory=list)
    converted_blocks: list[dict[str, Any]] = field(default_factory=list)
    plan: GenerationPlan | None = None
    planned_sections: list[PlannedSection] = field(default_factory=list)
    block_results: list[BlockResult] = field(default_factory=list)
    execution_blocks: list[dict[str, Any]] = field(default_factory=list)
    blocked_items: list[dict[str, Any]] = field(default_factory=list)
    section_outputs: list[dict[str, Any]] = field(default_factory=list)
    composed_document: ReportDocument | None = None
    validation_errors: list[str] = field(default_factory=list)
    rendered_output: Any = None
