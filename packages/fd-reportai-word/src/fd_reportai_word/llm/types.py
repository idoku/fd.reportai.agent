from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class SupportsInvoke(Protocol):
    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any: ...


@dataclass(slots=True)
class LlmProviderConfig:
    provider: str
    model: str | None = None
    temperature: float = 0.1
    api_key: str | None = None
    base_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
