from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .factory import LLMFactory
from .types import LlmProviderConfig, SupportsInvoke


@dataclass(slots=True)
class LLMLocator:
    provider: str = "mock"
    model: str | None = None
    temperature: float = 0.1
    api_key: str | None = None
    base_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def get_llm(self) -> SupportsInvoke:
        return LLMFactory.create(
            LlmProviderConfig(
                provider=self.provider,
                model=self.model,
                temperature=self.temperature,
                api_key=self.api_key,
                base_url=self.base_url,
                extra=dict(self.extra),
            )
        )
