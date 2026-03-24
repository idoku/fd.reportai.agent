from __future__ import annotations

from .registry import GLOBAL_LLM_REGISTRY
from .types import LlmProviderConfig, SupportsInvoke


class LLMFactory:
    @staticmethod
    def create(config: LlmProviderConfig) -> SupportsInvoke:
        return GLOBAL_LLM_REGISTRY.create(config)
