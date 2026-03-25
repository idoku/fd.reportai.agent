from __future__ import annotations

from ...config import ComputedFieldConfig, SectionElementConfig


LAND_COMPUTED_FIELDS = [
    ComputedFieldConfig(
        key="项目名称",
        mode="llm_text",
        prompt_file="land/project_name_prompt.txt",
        input_blocks=[
            SectionElementConfig(key="项目信息", required=False),
            SectionElementConfig(key="估价对象", required=False),
            SectionElementConfig(key="委托估价方", required=False),
        ],
    ),
]
