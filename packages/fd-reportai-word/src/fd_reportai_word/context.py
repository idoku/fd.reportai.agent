from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import ElementMap, WordPipelineConfig


@dataclass(slots=True)
class WordContext:
    framework: WordPipelineConfig | None = None
    elements: ElementMap = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    detections: list[dict[str, Any]] = field(default_factory=list)
    converted_blocks: list[dict[str, Any]] = field(default_factory=list)
    plan: list[dict[str, Any]] = field(default_factory=list)
    execution_blocks: list[dict[str, Any]] = field(default_factory=list)
    blocked_items: list[dict[str, Any]] = field(default_factory=list)
    section_outputs: list[dict[str, Any]] = field(default_factory=list)
    composed_document: Any = None
    validation_errors: list[str] = field(default_factory=list)
    rendered_output: Any = None
