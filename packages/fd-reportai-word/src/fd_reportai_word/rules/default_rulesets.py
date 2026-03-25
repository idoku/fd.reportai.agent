from __future__ import annotations

from ..config import DEFAULT_RULES_DIR, ReportSectionConfig, SectionElementConfig, WordPipelineConfig
from ..context import WordContext


def ruleset_land() -> WordPipelineConfig:
    return WordPipelineConfig(
        name="ruleset_land_v1",
        version="v1",
        title="土地估价报告",
        rules_dir=DEFAULT_RULES_DIR,
        sections=[
            ReportSectionConfig(
                key="cover",
                title="封面",
                block_mode="prompt_generation",
                prompt_file="land/cover_prompt.txt",
                template_file="land/land_cover.md",
                options={"template_name": "land/land_cover.md"},
                elements=[
                    SectionElementConfig(key="报告标题"),
                    SectionElementConfig(key="项目名称"),
                    SectionElementConfig(key="委托方"),
                    SectionElementConfig(key="报告编号"),
                    SectionElementConfig(key="提交日期"),
                ],
            )
        ],
    )


RULESET_LAND = ruleset_land()

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
