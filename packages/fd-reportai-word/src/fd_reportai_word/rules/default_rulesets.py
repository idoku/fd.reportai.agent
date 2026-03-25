from __future__ import annotations

from ..config import WordPipelineConfig
from ..context import WordContext
from .land.ruleset import RULESET_LAND, ruleset_land


DEFAULT_RULESETS: dict[str, WordPipelineConfig] = {
    "ruleset_land": RULESET_LAND,
}


def get_default_ruleset(name: str = "ruleset_land") -> WordPipelineConfig:
    try:
        return DEFAULT_RULESETS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown default ruleset: {name}") from exc


def apply_default_ruleset(context: WordContext, name: str = "ruleset_land") -> WordContext:
    if context.framework is None:
        context.framework = get_default_ruleset(name)
    return context
