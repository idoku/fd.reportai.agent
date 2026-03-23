from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"


@dataclass(slots=True)
class ValidationResult:
    is_valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass(slots=True)
class BlockTrace:
    template_version: str | None = None
    rule_version: str | None = None
    prompt_version: str | None = None
    model_version: str | None = None
    data_snapshot_id: str | None = None
    block_revision: int = 1
    input_snapshot: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
