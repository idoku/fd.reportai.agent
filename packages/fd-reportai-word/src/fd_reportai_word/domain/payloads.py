from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ElementValue:
    value: Any
    label: str | None = None
    type: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DataContext:
    values: dict[str, ElementValue] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    snapshot_id: str | None = None


@dataclass(slots=True)
class ResolvedInput:
    key: str
    source_key: str
    required: bool
    value: Any = None
    has_value: bool = False
    used_default: bool = False
    options: dict[str, Any] = field(default_factory=dict)
