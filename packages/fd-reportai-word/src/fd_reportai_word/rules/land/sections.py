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
            ContentItemConfig(
                key="地价定义",
                template_file="land/land_summary_value.md",
                elements=[
                    SectionElementConfig(key="估价对象界定"),
                    SectionElementConfig(key="估价期日", aliases=["查勘完成日期"], options={"transform": "cn_date"}),
                    SectionElementConfig(key="期日设定"),
                    SectionElementConfig(key="用途设定"),
                    SectionElementConfig(key="权利类型设定"),
                    SectionElementConfig(key="年限设定"),
                    SectionElementConfig(key="利用条件设定"),
                    SectionElementConfig(key="开发程度设定"),
                    SectionElementConfig(key="他项权利设定"),
                    SectionElementConfig(key="价格内涵总结"),
                ],
            ),
            ContentItemConfig(
                key="估价结果",
                template_file="land/land_summary_result.md",
                elements=[
                    SectionElementConfig(key="估价结果描述"),
                    SectionElementConfig(key="估价结果说明"),
                ],
            ),
            ContentItemConfig(
                key="估价师签字",
                template_file="land/land_summary_signatures.md",
                elements=[
                    SectionElementConfig(key="估价师签字"),
                ],
            ),
            ContentItemConfig(
                key="土地估价机构",
                template_file="land/land_summary_agency.md",
                elements=[
                    SectionElementConfig(
                        key="估价机构法定代表人签字",
                        aliases=["法定代表人签字", "法定代表人签字图片", "法人签名"],
                        options={"transform": "markdown_image"},
                    ),
                    SectionElementConfig(key="土地估价机构", aliases=["估价机构"]),
                    SectionElementConfig(key="估价日期", aliases=["报告完成日期"], options={"transform": "cn_date"}),
                ],
            ),
            ContentItemConfig(
                key="结果一览表",
                template_file="land/land_summary_table.md",
                elements=[
                    SectionElementConfig(key="估价机构", aliases=["土地估价机构"]),
                    SectionElementConfig(key="估价报告编号", source_key="报告编号"),
                    SectionElementConfig(key="估价期日", aliases=["查勘完成日期"]),
                    SectionElementConfig(key="估价目的"),
                    SectionElementConfig(
                        key="估价期日的土地使用权性质",
                        aliases=["土地使用权性质", "权利性质"],
                    ),
                    SectionElementConfig(key="结果一览表表格"),
                    SectionElementConfig(
                        key="结果一览表备注",
                        required=False,
                        default_value="“五通”为通路、通电、通讯、供水、排水。",
                    ),
                    SectionElementConfig(
                        key="限定条件",
                        required=False,
                        default_value="",
                        options={"transform": "numbered_paragraphs"},
                    ),
                    SectionElementConfig(
                        key="其他说明事项",
                        required=False,
                        default_value="",
                        options={"transform": "numbered_paragraphs"},
                    ),
                    SectionElementConfig(key="落款机构", source_key="估价机构", aliases=["土地估价机构"]),
                    SectionElementConfig(
                        key="落款日期",
                        source_key="报告完成日期",
                        aliases=["估价日期"],
                        options={"transform": "cn_date"},
                    ),
                ],
            ),
        ],
    ),
]
