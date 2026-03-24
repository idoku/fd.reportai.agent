from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TemplateBlockConfig:
    key: str
    title: str
    input_keys: list[str] = field(default_factory=list)
    prompt_file: str | None = None
    template_file: str | None = None
    output_fields: list[str] = field(default_factory=list)
    provider: str | None = None
    model: str | None = None


LAND_COVER_BLOCK = TemplateBlockConfig(
    key="cover",
    title="封面",
    input_keys=["项目信息", "估价对象"],
    prompt_file="land/cover_prompt.txt",
    template_file="land/land_cover.md",
    output_fields=["报告标题", "项目名称", "委托方", "报告编号", "提交日期"],
)


LAND_BLOCKS: dict[str, TemplateBlockConfig] = {
    LAND_COVER_BLOCK.key: LAND_COVER_BLOCK,
}
