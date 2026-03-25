from __future__ import annotations

from ...config import ReportSectionConfig, SectionElementConfig


LAND_SECTIONS = [
    ReportSectionConfig(
        key="cover",
        title="封面",
        block_mode="template_fill",
        template_file="land/land_cover.md",
        elements=[
            SectionElementConfig(key="报告标题"),
            SectionElementConfig(key="项目名称"),
            SectionElementConfig(key="委托方"),
            SectionElementConfig(key="报告编号"),
            SectionElementConfig(key="提交日期"),
        ],
    )
]
