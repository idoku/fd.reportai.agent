from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


LAND_INPUT_PATH = Path(__file__).resolve().parents[6] / "inputs" / "land_input.json"


@dataclass(slots=True, frozen=True)
class FieldMetadata:
    key: str
    group: str
    status: str = "active"
    owner: str | None = None
    aliases: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    relations: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # 新增：来源/去向/优先级
    source: str | None = None
    feeds_into: tuple[str, ...] = ()
    priority: int = 0


@dataclass(slots=True, frozen=True)
class FieldGroup:
    name: str
    entries: tuple[FieldMetadata, ...]


def field(
    key: str,
    *,
    aliases: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
    status: str = "active",
    owner: str | None = None,
    relations: dict[str, tuple[str, ...]] | None = None,
    source: str | None = None,
    feeds_into: tuple[str, ...] = (),
    priority: int = 0,
) -> FieldMetadata:
    return FieldMetadata(
        key=key,
        group="",
        status=status,
        owner=owner,
        aliases=aliases,
        notes=notes,
        relations=relations or {},
        source=source,
        feeds_into=feeds_into,
        priority=priority,
    )


STRUCTURED_COMPUTED_FIELD_LEAVES: dict[str, tuple[tuple[str, str], ...]] = {
    "地价定义分项设定": (
        ("用途设定", "scalar"),
        ("权利类型设定", "scalar"),
        ("年限设定", "scalar"),
        ("利用条件设定", "scalar"),
        ("开发程度设定", "scalar"),
        ("他项权利设定", "scalar"),
    ),
}


# ---------------------------------------------------------------------------
# 内置 (Python) 字段数据 —— 作为 xlsx 无法加载时的兜底，也保留原始参考
# 人类管理请直接编辑: land_fields.xlsx（同目录）
# ---------------------------------------------------------------------------

_BUILTIN_FIELD_GROUPS: tuple[FieldGroup, ...] = (
    FieldGroup(
        name="输入",
        entries=(
            field("项目信息"),
            field("常量"),
            field("委托估价方"),
            field("估价对象"),
            field("一般因素"),
            field("区域因素"),
            field("国家法律法规"),
            field("地方法律法规"),
            field("有关技术标准"),
            field("估价依据"),
            field("估价原则"),
            field("报告的使用", aliases=("估价结果和估价报告的使用",)),
            field("变现能力分析"),
            field("附件清单"),
            field("估价师"),
            field("法人签名", aliases=("法定代表人签字", "法定代表人签字图片")),
        ),
    ),
    FieldGroup(
        name="计算",
        entries=(
            field("项目名称"),
            field("委托方与权利人关系"),
            field("估价目的描述"),
            field("估价对象界定"),
            field("地价定义概述"),
            field("土地登记状况描述"),
            field("不动产权证书"),
            field("土地权利状况"),
            field("土地利用状况"),
            field("个别因素说明"),
            field(
                "地价定义分项设定",
                notes=("结构化计算字段，包含用途/权利/年限/利用条件/开发程度/他项权利 6 个叶子字段。",),
            ),
            field("价格内涵总结"),
            field("估价结果描述"),
            field("估价结果说明"),
            field("委托方资料"),
            field("现场查勘资料"),
            field("方法选择"),
            field("前提条件"),
            field("特殊事项说明"),
            field("估价师签字"),
            field("结果一览表表格"),
        ),
    ),
    FieldGroup(
        name="计算叶子",
        entries=(
            field("用途设定"),
            field("权利类型设定"),
            field("年限设定"),
            field("利用条件设定"),
            field("开发程度设定"),
            field("他项权利设定"),
        ),
    ),
    FieldGroup(
        name="章节字段",
        entries=(
            field("委托方"),
            field("提交日期"),
            field("估价期日"),
            field("估价内涵"),
            field("委托估价方联系人"),
            field("委托估价方联系方式"),
            field("土地估价机构"),
            field("估价机构法定代表人签字"),
            field("估价报告编号"),
            field("估价期日的土地使用权性质", aliases=("土地使用权性质", "权利性质")),
            field("结果一览表备注"),
            field("限定条件"),
            field("其他说明事项"),
            field("估价结果"),
            field("附件清单正文"),
        ),
    ),
)


def build_field_metadata_index(groups: tuple[FieldGroup, ...] = ...) -> dict[str, FieldMetadata]:  # type: ignore[assignment]
    if groups is ...:  # type: ignore[comparison-overlap]
        groups = FIELD_GROUPS
    index: dict[str, FieldMetadata] = {}
    for group in groups:
        for entry in group.entries:
            index[entry.key] = FieldMetadata(
                key=entry.key,
                group=group.name,
                status=entry.status,
                owner=entry.owner,
                aliases=entry.aliases,
                notes=entry.notes,
                relations=dict(entry.relations),
                source=entry.source,
                feeds_into=entry.feeds_into,
                priority=entry.priority,
            )
    return index


# ---------------------------------------------------------------------------
# 运行时加载：优先从 land_fields.xlsx 读取，xlsx 不存在或读取失败则回退到内置数据
# ---------------------------------------------------------------------------

_XLSX_PATH = Path(__file__).resolve().parent / "land_fields.xlsx"


def _load_field_groups() -> tuple[FieldGroup, ...]:
    if _XLSX_PATH.exists():
        try:
            from .field_registry_loader import load_field_registry_xlsx  # noqa: PLC0415
            return load_field_registry_xlsx(_XLSX_PATH)
        except Exception:
            pass
    return _BUILTIN_FIELD_GROUPS


def _load_structured_computed_leaves() -> dict[str, tuple[tuple[str, str], ...]]:
    if _XLSX_PATH.exists():
        try:
            from .field_registry_loader import load_structured_computed_leaves_from_xlsx  # noqa: PLC0415
            leaves = load_structured_computed_leaves_from_xlsx(_XLSX_PATH)
            if leaves:
                return leaves
        except Exception:
            pass
    return STRUCTURED_COMPUTED_FIELD_LEAVES


FIELD_GROUPS: tuple[FieldGroup, ...] = _load_field_groups()
STRUCTURED_COMPUTED_FIELD_LEAVES = _load_structured_computed_leaves()
FIELD_METADATA = build_field_metadata_index(FIELD_GROUPS)

