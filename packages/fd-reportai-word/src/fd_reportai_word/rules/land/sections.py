from __future__ import annotations

from ...config import ContentItemConfig, ReportSectionConfig, SectionElementConfig


LAND_SECTIONS = [
    ReportSectionConfig(
        key="cover",
        title="封面",
        block_mode="template_fill",
        template_file="land/land_cover.md",
        elements=[
            SectionElementConfig(key="报告标题", default_value="土地估价报告"),
            SectionElementConfig(key="项目名称"),
            SectionElementConfig(key="委托方", aliases=["委托方名称"]),
            SectionElementConfig(key="报告编号"),
            SectionElementConfig(key="提交日期", aliases=["报告完成日期"], options={"transform": "cn_date"}),
        ],
    ),
    ReportSectionConfig(
        key="summary",
        title="摘要",
        block_mode="template_fill",
        template_file="land/land_summary.md",
        elements=[
            SectionElementConfig(key="项目名称"),
            SectionElementConfig(key="估价期日", aliases=["查勘完成日期"], options={"transform": "cn_date"}),
            SectionElementConfig(key="估价日期", aliases=["报告完成日期"], options={"transform": "cn_date"}),
            
        ],
        content_items=[
            ContentItemConfig(
                key="委托估价方",
                template_file="land/land_summary_client.md",
                elements=[
                    SectionElementConfig(key="委托估价方", source_key="委托方", aliases=["委托方名称"]),
                    SectionElementConfig(key="委托估价方联系人", source_key="联系人"),
                    SectionElementConfig(key="委托估价方联系方式", source_key="联系方式"),
                    SectionElementConfig(key="委托方与权利人关系"),
                ],
            ),
            ContentItemConfig(
                key="估价目的",
                template_file="land/land_summary_purpose.md",
                elements=[
                    SectionElementConfig(key="估价目的描述"),
                ],
            ),
        ],
    ),
]
