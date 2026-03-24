from __future__ import annotations

from .config import DEFAULT_RULES_DIR, ReportSectionConfig, SectionElementConfig, WordPipelineConfig


def land_conver_v1() -> WordPipelineConfig:
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
                    SectionElementConfig(key="report_title"),
                    SectionElementConfig(key="project_name"),
                    SectionElementConfig(key="entrusting_party"),
                    SectionElementConfig(key="report_number"),
                    SectionElementConfig(key="submit_date"),
                ],
            )
        ],
    )


def valuation_report_v1() -> WordPipelineConfig:
    return WordPipelineConfig(
        name="valuation_report_v1",
        version="v1",
        title="Valuation Report",
        rules_dir=DEFAULT_RULES_DIR,
        sections=[
            ReportSectionConfig(
                key="summary",
                title="Summary",
                block_mode="template_fill",
                template_file="valuation/summary.md",
                elements=[
                    SectionElementConfig(key="project_name"),
                    SectionElementConfig(key="valuation_conclusion"),
                ],
            ),
            ReportSectionConfig(
                key="key_metrics",
                title="Key Metrics",
                block_mode="computed",
                block_type="table",
                compute_key="build_metrics_table",
                elements=[
                    SectionElementConfig(key="income"),
                    SectionElementConfig(key="ebitda"),
                ],
            ),
            ReportSectionConfig(
                key="analysis",
                title="Analysis",
                block_mode="prompt_generation",
                prompt_file="valuation/analysis.prompt.md",
                elements=[
                    SectionElementConfig(key="project_name"),
                    SectionElementConfig(key="valuation_conclusion"),
                ],
            ),
            ReportSectionConfig(
                key="site_photos",
                title="Site Photos",
                block_mode="computed",
                block_type="image_group",
                compute_key="build_site_photos",
                elements=[
                    SectionElementConfig(key="photos", required=False, default_value=[]),
                ],
            ),
        ],
    )
