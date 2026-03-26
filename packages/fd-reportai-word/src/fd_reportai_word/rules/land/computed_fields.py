from __future__ import annotations

from ...config import ComputedFieldConfig, SectionElementConfig


LAND_COMPUTED_FIELDS = [
    ComputedFieldConfig(
        key="项目名称",
        mode="llm_text",
        prompt_file="land/project_name_prompt.txt",
        input_blocks=[
            SectionElementConfig(key="项目信息", required=True),
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=True),
        ],
    ),
    ComputedFieldConfig(
        key="委托方与权利人关系",
        mode="llm_text",
        prompt_file="land/client_owner_relation_prompt.txt",
        input_blocks=[
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=True),
        ],
    ),
     ComputedFieldConfig(
        key="估价目的描述",
        mode="llm_text",
        prompt_file="land/valuation_purpose_prompt.txt",
        input_blocks=[
            SectionElementConfig(key="估价对象", required=True),
            SectionElementConfig(key="委托估价方", required=True),
            SectionElementConfig(key="估价依据", required=True),
        ],
    ),
]
