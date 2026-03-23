from __future__ import annotations

from .config import ReportSectionConfig, SectionElementConfig, WordPipelineConfig


def valuation_report_v1() -> WordPipelineConfig:
    return WordPipelineConfig(
        name="valuation_report_v1",
        version="v1",
        title="Valuation Report",
        sections=[
            ReportSectionConfig(
                key="summary",
                title="Summary",
                block_mode="template_fill",
                template="Project: {project_name}\nValuation conclusion: {valuation_conclusion}",
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
