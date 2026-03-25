from __future__ import annotations

from ...config import ReportSectionConfig, SectionElementConfig


LAND_SECTIONS = [
    ReportSectionConfig(
        key="cover",
        title="封面",
        block_mode="template_fill",
        template_file="land/land_cover.md",
        elements=[
            SectionElementConfig(key="报告标题", default_value="土地估价报告"),
            SectionElementConfig(key="项目名称"),
            SectionElementConfig(key="委托方", source_key="委托估价方.委托方名称"),
            SectionElementConfig(key="报告编号", source_key="项目信息.报告编号"),
            SectionElementConfig(
                key="提交日期",
                source_key="项目信息.报告完成日期",
                options={"transform": "cn_date"},
            ),
        ],
    )
]
