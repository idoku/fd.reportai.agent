from __future__ import annotations

from ..config import DEFAULT_RULES_DIR, ReportSectionConfig, SectionElementConfig, WordPipelineConfig
from ..context import WordContext


def land_conver_ruleset() -> WordPipelineConfig:
    return WordPipelineConfig(
        name="land_conver_v1",
        version="v1",
        title="土地估价报告",
        rules_dir=DEFAULT_RULES_DIR,
        sections=[
            ReportSectionConfig(
                key="conver",
                title="封面",
                block_mode="template_fill",
                template_file="land/land_cover.md",
                elements=[
                    SectionElementConfig(key="报告标题", source_key="report_title"),
                    SectionElementConfig(key="项目名称", source_key="project_name"),
                    SectionElementConfig(key="委托方", source_key="entrusting_party"),
                    SectionElementConfig(key="报告编号", source_key="report_number"),
                    SectionElementConfig(key="提交日期", source_key="submit_date"),
                ],
            ),
            ReportSectionConfig(
                key="summary",
                title="摘要",
                block_mode="template_fill",
                template_file="land/land_summary.md",
                elements=[
                    SectionElementConfig(key="估价项目名称", required=False),
                    SectionElementConfig(key="委托估价方", required=False),
                    SectionElementConfig(key="联系人", required=False),
                    SectionElementConfig(key="联系方式", required=False),
                    SectionElementConfig(key="委托方与权利人关系", required=False),
                    SectionElementConfig(key="估价目的", required=False),
                    SectionElementConfig(key="估价期日", required=False),
                    SectionElementConfig(key="估价日期", required=False),
                    SectionElementConfig(key="地价定义", required=False),
                    SectionElementConfig(key="估价结果说明", required=False),
                    SectionElementConfig(key="估价结果明细", required=False),
                    SectionElementConfig(key="估价结果合计", required=False),
                    SectionElementConfig(key="土地估价师签字表", required=False),
                    SectionElementConfig(key="估价机构法定代表人签字", required=False, default_value=""),
                    SectionElementConfig(key="估价机构", required=False),
                    SectionElementConfig(key="摘要出具日期", required=False),
                    SectionElementConfig(key="结果一览表机构信息", required=False),
                    SectionElementConfig(key="结果一览表目的与权性质", required=False),
                    SectionElementConfig(key="结果一览表表格", required=False),
                    SectionElementConfig(key="结果一览表备注", required=False),
                    SectionElementConfig(key="限定条件", required=False),
                    SectionElementConfig(key="其他说明事项", required=False),
                ],
            ),
        ],
    )


LAND_CONVER_RULESET = land_conver_ruleset()

DEFAULT_RULESETS: dict[str, WordPipelineConfig] = {
    "land_conver": LAND_CONVER_RULESET,
}


def get_default_ruleset(name: str = "land_conver") -> WordPipelineConfig:
    try:
        return DEFAULT_RULESETS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown default ruleset: {name}") from exc


def apply_default_ruleset(context: WordContext, name: str = "land_conver") -> WordContext:
    if context.framework is None:
        context.framework = get_default_ruleset(name)
    return context
