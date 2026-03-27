from __future__ import annotations

from ...config import DEFAULT_RULES_DIR, ReportSectionConfig, SectionElementConfig, WordPipelineConfig
from .computed_fields import LAND_COMPUTED_FIELDS
from .sections import LAND_SECTIONS


def _make_ruleset(name: str, title: str, sections: list[ReportSectionConfig]) -> WordPipelineConfig:
    return WordPipelineConfig(
        name=name,
        version="v1",
        title=title,
        rules_dir=DEFAULT_RULES_DIR,
        computed_fields=list(LAND_COMPUTED_FIELDS),
        sections=sections,
    )


def _cover_section() -> ReportSectionConfig:
    return LAND_SECTIONS[0]


def _summary_section() -> ReportSectionConfig:
    return LAND_SECTIONS[1]


def _object_definition_section() -> ReportSectionConfig:
    return ReportSectionConfig(
        key="object_definition",
        title="估价对象界定",
        block_mode="template_fill",
        template_file="land/object_definition/_template.md",
        elements=[
            SectionElementConfig(key="委托估价方", source_key="委托方", aliases=["委托方名称"]),
            SectionElementConfig(key="委托估价方联系人", source_key="联系人"),
            SectionElementConfig(key="委托估价方联系方式", source_key="联系方式"),
            SectionElementConfig(key="委托方与权利人关系"),
            SectionElementConfig(key="土地登记状况", required=False),
            SectionElementConfig(key="估价对象界定"),
            SectionElementConfig(key="估价期日", aliases=["查勘完成日期"], options={"transform": "cn_date"}),
            SectionElementConfig(key="用途设定"),
            SectionElementConfig(key="权利类型设定"),
            SectionElementConfig(key="年限设定"),
            SectionElementConfig(key="利用条件设定"),
            SectionElementConfig(key="开发程度设定"),
            SectionElementConfig(key="他项权利设定"),
            SectionElementConfig(key="价格内涵总结"),
        ],
    )


def _result_usage_section() -> ReportSectionConfig:
    return ReportSectionConfig(
        key="result_usage",
        title="土地估价结果及其使用",
        block_mode="template_fill",
        template_file="land/result_usage/_template.md",
        elements=[
            SectionElementConfig(key="估价依据", required=False, default_value=""),
            SectionElementConfig(key="土地估价", source_key="估价结果描述", required=False, default_value=""),
            SectionElementConfig(
                key="估价结果和估价报告的使用",
                source_key="估价结果说明",
                required=False,
                default_value="",
            ),
        ],
    )


def _attachments_section() -> ReportSectionConfig:
    return ReportSectionConfig(
        key="attachments",
        title="附件",
        block_mode="template_fill",
        template_file="land/attachments/_template.md",
        elements=[],
    )


def ruleset_land() -> WordPipelineConfig:
    return _make_ruleset(
        name="ruleset_land_v1",
        title="土地估价报告",
        sections=list(LAND_SECTIONS),
    )


def ruleset_land_cover() -> WordPipelineConfig:
    return _make_ruleset(
        name="ruleset_land_cover_v1",
        title="土地估价报告-封面",
        sections=[_cover_section()],
    )


def ruleset_land_summary() -> WordPipelineConfig:
    return _make_ruleset(
        name="ruleset_land_summary_v1",
        title="土地估价报告-摘要",
        sections=[_summary_section()],
    )


def ruleset_land_object_definition() -> WordPipelineConfig:
    return _make_ruleset(
        name="ruleset_land_object_definition_v1",
        title="土地估价报告-估价对象界定",
        sections=[_object_definition_section()],
    )


def ruleset_land_result_usage() -> WordPipelineConfig:
    return _make_ruleset(
        name="ruleset_land_result_usage_v1",
        title="土地估价报告-土地估价结果及其使用",
        sections=[_result_usage_section()],
    )


def ruleset_land_attachments() -> WordPipelineConfig:
    return _make_ruleset(
        name="ruleset_land_attachments_v1",
        title="土地估价报告-附件",
        sections=[_attachments_section()],
    )


RULESET_LAND = ruleset_land()
RULESET_LAND_COVER = ruleset_land_cover()
RULESET_LAND_SUMMARY = ruleset_land_summary()
RULESET_LAND_OBJECT_DEFINITION = ruleset_land_object_definition()
RULESET_LAND_RESULT_USAGE = ruleset_land_result_usage()
RULESET_LAND_ATTACHMENTS = ruleset_land_attachments()
