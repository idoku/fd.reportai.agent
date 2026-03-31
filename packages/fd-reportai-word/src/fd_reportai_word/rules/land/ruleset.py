from __future__ import annotations

from ...config import DEFAULT_RULES_DIR, ReportSectionConfig, WordPipelineConfig
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
    return LAND_SECTIONS[2]


def _result_usage_section() -> ReportSectionConfig:
    return LAND_SECTIONS[3]


def _attachments_section() -> ReportSectionConfig:
    return LAND_SECTIONS[4]


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
