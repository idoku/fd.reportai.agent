from __future__ import annotations

from ...config import ComputedFieldConfig, SectionElementConfig


LAND_COMPUTED_FIELDS = [
    ComputedFieldConfig(
        key="项目名称",
        mode="llm_text",
        prompt_file="land/computed/project_name.md",
        input_blocks=[
            SectionElementConfig(key="项目信息", required=True),
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="委托方与权利人关系",
        mode="llm_text",
        prompt_file="land/computed/client_owner_relation.md",
        input_blocks=[
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="估价目的描述",
        mode="llm_text",
        prompt_file="land/computed/valuation_purpose.md",
        input_blocks=[
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=True),
            SectionElementConfig(key="估价依据", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="估价对象界定",
        mode="llm_text",
        prompt_file="land/computed/valuation_object_scope.md",
        input_blocks=[
            SectionElementConfig(key="项目信息", required=True),
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=False),
        ],
    ),
    ComputedFieldConfig(
        key="地价定义分项设定",
        mode="llm_json",
        prompt_file="land/computed/valuation_definition_items.md",
        input_blocks=[
            SectionElementConfig(key="项目信息", required=True),
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=False),
            SectionElementConfig(key="估价依据", required=False),
        ],
    ),
    ComputedFieldConfig(
        key="价格内涵总结",
        mode="llm_text",
        prompt_file="land/computed/valuation_connotation.md",
        input_blocks=[
            SectionElementConfig(key="项目信息", required=True),
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="地价定义分项设定", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="估价结果描述",
        mode="llm_text",
        prompt_file="land/computed/valuation_result_description.md",
        input_blocks=[
            SectionElementConfig(key="项目信息", required=True),
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=True),
            SectionElementConfig(key="地价定义分项设定", required=False),
        ],
    ),
    ComputedFieldConfig(
        key="估价结果说明",
        mode="llm_text",
        prompt_file="land/computed/valuation_result.md",
        input_blocks=[
            SectionElementConfig(key="估价对象", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="估价师签字",
        mode="llm_text",
        prompt_file="land/computed/valuation_signatures.md",
        input_blocks=[
            SectionElementConfig(key="估价师", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="结果一览表表格",
        mode="extract",
        options={
            "path": "估价对象",
            "transform": "land_result_table",
        },
    ),
]
