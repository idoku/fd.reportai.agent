from __future__ import annotations

from ...config import DEFAULT_RULES_DIR, WordPipelineConfig
from .computed_fields import LAND_COMPUTED_FIELDS
from .sections import LAND_SECTIONS


def ruleset_land() -> WordPipelineConfig:
    return WordPipelineConfig(
        name="ruleset_land_v1",
        version="v1",
        title="土地估价报告",
        rules_dir=DEFAULT_RULES_DIR,
        computed_fields=list(LAND_COMPUTED_FIELDS),
        sections=list(LAND_SECTIONS),
    )


RULESET_LAND = ruleset_land()
