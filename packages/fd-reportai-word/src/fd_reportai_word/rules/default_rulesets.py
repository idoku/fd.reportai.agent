from __future__ import annotations

from ..config import WordPipelineConfig
from ..context import WordContext
from .land.ruleset import (
    RULESET_LAND,
    RULESET_LAND_ATTACHMENTS,
    RULESET_LAND_COVER,
    RULESET_LAND_OBJECT_DEFINITION,
    RULESET_LAND_RESULT_USAGE,
    RULESET_LAND_SUMMARY,
    ruleset_land,
    ruleset_land_attachments,
    ruleset_land_cover,
    ruleset_land_object_definition,
    ruleset_land_result_usage,
    ruleset_land_summary,
)


DEFAULT_RULESETS: dict[str, WordPipelineConfig] = {
    "ruleset_land": RULESET_LAND,
    "ruleset_land_cover": RULESET_LAND_COVER,
    "ruleset_land_summary": RULESET_LAND_SUMMARY,
    "ruleset_land_object_definition": RULESET_LAND_OBJECT_DEFINITION,
    "ruleset_land_result_usage": RULESET_LAND_RESULT_USAGE,
    "ruleset_land_attachments": RULESET_LAND_ATTACHMENTS,
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
