from __future__ import annotations

from ...config import ComputedFieldConfig, SectionElementConfig


LAND_COMPUTED_FIELDS = [
    ComputedFieldConfig(
        key="项目名称",
        mode="llm_text",
        prompt_file="land/computed/项目名称.prompt.txt",
        input_blocks=[
            SectionElementConfig(key="项目信息", required=True),
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="委托方与权利人关系",
        mode="llm_text",
        prompt_file="land/computed/委托方与权利人关系.prompt.txt",
        input_blocks=[
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="估价目的描述",
        mode="llm_text",
        prompt_file="land/computed/估价目的描述.prompt.txt",
        examples_file="land/computed/估价目的描述.examples.json",
        input_blocks=[
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=True),
            SectionElementConfig(key="估价依据", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="估价对象界定",
        mode="llm_text",
        prompt_file="land/computed/估价对象界定.prompt.txt",
        examples_file="land/computed/估价对象界定.examples.json",
        input_blocks=[
            SectionElementConfig(key="项目信息", required=True),
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=False),
        ],
    ),
    ComputedFieldConfig(
        key="土地登记状况描述",
        mode="llm_text",
        prompt_file="land/computed/土地登记状况描述.prompt.txt",
        input_blocks=[
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=False),
        ],
    ),
    ComputedFieldConfig(
        key="不动产权证书",
        mode="llm_table",
        prompt_file="land/computed/土地登记状况.prompt.txt",
        template_file="land/object_definition/3.object.table.template.md",
        input_blocks=[
            SectionElementConfig(key="估价对象", required=True),
        ],
        options={
            "max_tokens": 1200,
        },
    ),
    ComputedFieldConfig(
        key="地价定义分项设定",
        mode="llm_json",
        prompt_file="land/computed/地价定义分项设定.prompt.txt",
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
        prompt_file="land/computed/价格内涵总结.prompt.txt",
        input_blocks=[
            SectionElementConfig(key="项目信息", required=True),
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="地价定义分项设定", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="估价结果描述",
        mode="llm_text",
        prompt_file="land/computed/估价结果描述.prompt.txt",
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
        prompt_file="land/computed/估价结果说明.prompt.txt",
        input_blocks=[
            SectionElementConfig(key="估价对象", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="估价师签字",
        mode="llm_text",
        prompt_file="land/computed/估价师签字.prompt.txt",
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
