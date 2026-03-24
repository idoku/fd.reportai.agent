from __future__ import annotations

from collections.abc import Callable

from .types import LlmProviderConfig, SupportsInvoke


LlmBuilder = Callable[[LlmProviderConfig], SupportsInvoke]


class LlmRegistry:
    def __init__(self) -> None:
        self._builders: dict[str, LlmBuilder] = {}

    def register(self, provider: str, builder: LlmBuilder) -> None:
        self._builders[provider.strip().lower()] = builder

    def get(self, provider: str) -> LlmBuilder:
        normalized = provider.strip().lower()
        if normalized not in self._builders:
            raise KeyError(f"LLM provider is not registered: {provider}")
        return self._builders[normalized]

    def create(self, config: LlmProviderConfig) -> SupportsInvoke:
        return self.get(config.provider)(config)

    def providers(self) -> list[str]:
        return sorted(self._builders.keys())


GLOBAL_LLM_REGISTRY = LlmRegistry()
