from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .definitions import BlockDefinition, SectionDefinition
from .payloads import ResolvedInput
from .traces import BlockTrace, ValidationResult


@dataclass(slots=True)
class BlockTask:
    section_key: str
    section_title: str
    definition: BlockDefinition
    resolved_inputs: list[ResolvedInput] = field(default_factory=list)
    missing_required_inputs: list[str] = field(default_factory=list)
    children: list["BlockTask"] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PlannedSection:
    definition: SectionDefinition
    tasks: list[BlockTask] = field(default_factory=list)
    children: list["PlannedSection"] = field(default_factory=list)


@dataclass(slots=True)
class BlockResult:
    section_key: str
    block_key: str
    title: str
    block_type: str
    generator_mode: str
    content: Any
    resolved_inputs: list[ResolvedInput] = field(default_factory=list)
    missing_required_inputs: list[str] = field(default_factory=list)
    trace: BlockTrace = field(default_factory=BlockTrace)
    validation: ValidationResult = field(default_factory=ValidationResult)
    options: dict[str, Any] = field(default_factory=dict)
