from __future__ import annotations

from pathlib import Path
import re
from typing import Any


def apply_transform(value: object | None, transform: object, metadata: dict[str, Any]) -> object | None:
    if value is None or transform is None:
        return value
    if transform == "cn_date":
        return to_chinese_date(str(value))
    if transform == "markdown_image":
        return to_markdown_image(str(value), metadata)
    if transform == "numbered_paragraphs":
        return to_numbered_paragraphs(value)
    if transform == "land_result_org_info":
        return to_land_result_org_info(value)
    if transform == "land_result_purpose_rights":
        return to_land_result_purpose_rights(value)
    if transform == "land_result_table":
        return to_land_result_table(value)
    raise ValueError(f"Unsupported transform: {transform}.")


def to_chinese_date(value: str) -> str:
    match = re.fullmatch(r"\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*", value)
    if not match:
        return value
    year, month, day = match.groups()
    digits = {"0": "〇", "1": "一", "2": "二", "3": "三", "4": "四", "5": "五", "6": "六", "7": "七", "8": "八", "9": "九"}
    return f"{''.join(digits[ch] for ch in year)}年{to_chinese_number(int(month))}月{to_chinese_number(int(day))}日"


def to_chinese_number(value: int) -> str:
    digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
    if value < 10:
        return digits[value]
    if value == 10:
        return "十"
    if value < 20:
        return "十" + digits[value % 10]
    tens, ones = divmod(value, 10)
    if ones == 0:
        return digits[tens] + "十"
    return digits[tens] + "十" + digits[ones]


def to_markdown_image(value: str, metadata: dict[str, Any]) -> str:
    image_path = value.strip()
    if not image_path:
        return ""
    resolved_path = resolve_media_path(image_path, metadata)
    return f"![法定代表人签字](<{resolved_path}>)"


def resolve_media_path(value: str, metadata: dict[str, Any]) -> str:
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        return value
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate.as_posix()
    input_base_dir = metadata.get("input_base_dir")
    if isinstance(input_base_dir, str) and input_base_dir.strip():
        return (Path(input_base_dir) / candidate).resolve().as_posix()
    return candidate.as_posix()


def to_numbered_paragraphs(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, list):
        return str(value)
    lines: list[str] = []
    for index, item in enumerate(value, start=1):
        item_text = stringify(item).strip()
        if not item_text:
            continue
        lines.append(f"\t{index}、{item_text}")
    return "\n".join(lines)


def to_land_result_org_info(value: object) -> str:
    info = value if isinstance(value, dict) else {}
    return (
        f"估价机构：{pick(info, '估价机构', '土地估价机构')}"
        f"    估价报告编号：{pick(info, '报告编号', '估价报告编号')}"
        f"    估价期日：{pick(info, '查勘完成日期', '估价期日')}"
    ).strip()


def to_land_result_purpose_rights(value: object) -> str:
    info = value if isinstance(value, dict) else {}
    return (
        f"估价目的：{pick(info, '估价目的')}"
        f"    估价期日的土地使用权性质："
        f"{pick(info, '估价期日的土地使用权性质', '土地使用权性质', '权利性质')}"
    ).strip()


def to_land_result_table(value: object) -> str:
    items = value if isinstance(value, list) else []
    rows = [
        [
            "估价期日的土地使用者",
            "宗地编号",
            "宗地名称",
            "不动产权证书证号",
            "用途-证载（或批准）",
            "用途-实际",
            "用途-设定",
            "容积率-规划",
            "容积率-实际",
            "容积率-设定",
            "土地开发程度-实际",
            "土地开发程度-设定",
            "剩余土地使用权年限/年",
            "面积/m2",
            "单位面积地价/元/m2",
            "总地价/元",
            "备注",
        ]
    ]

    detail_items: list[dict[str, Any]] = []
    total_info: dict[str, Any] | None = None
    for item in items:
        if not isinstance(item, dict):
            continue
        if "合计" in item and isinstance(item["合计"], dict):
            total_info = item["合计"]
            continue
        detail_items.append(item)

    for item in detail_items:
        usage = item.get("用途") if isinstance(item.get("用途"), dict) else {}
        ratio = item.get("容积率") if isinstance(item.get("容积率"), dict) else {}
        dev = item.get("开发程度") if isinstance(item.get("开发程度"), dict) else {}
        rows.append(
            [
                stringify(item.get("土地使用者")),
                stringify(item.get("宗地编号")),
                stringify(item.get("宗地名称")),
                stringify(item.get("不动产权证书证号")),
                stringify(usage.get("证载")),
                stringify(usage.get("实际")),
                stringify(usage.get("设定")),
                stringify(ratio.get("规划")),
                stringify(ratio.get("实际")),
                stringify(ratio.get("设定")),
                stringify(dev.get("实际")),
                stringify(dev.get("设定")),
                stringify(item.get("剩余年限")),
                stringify(item.get("面积_平方米")),
                stringify(item.get("单价_元")),
                stringify(item.get("总地价_元")),
                stringify(item.get("备注"), default="/"),
            ]
        )

    if total_info is None:
        total_info = {
            "面积_平方米": sum(to_number(item.get("面积_平方米")) for item in detail_items),
            "总地价_元": sum(to_number(item.get("总地价_元")) for item in detail_items),
        }

    rows.append(
        [
            "总计",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            stringify(total_info.get("面积_平方米")),
            "/",
            stringify(total_info.get("总地价_元")),
            "/",
        ]
    )
    return render_markdown_table(rows)


def render_markdown_table(rows: list[list[object]]) -> str:
    if not rows:
        return ""
    normalized = [[escape_table_cell(cell) for cell in row] for row in rows]
    header = "| " + " | ".join(normalized[0]) + " |"
    separator = "| " + " | ".join("---" for _ in normalized[0]) + " |"
    data_rows = ["| " + " | ".join(row) + " |" for row in normalized[1:]]
    return "\n".join([header, separator, *data_rows])


def escape_table_cell(value: object) -> str:
    return stringify(value).replace("\n", "<br>").replace("|", "\\|")


def stringify(value: object, *, default: str = "/") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = value.strip()
        return text if text else default
    return str(value)


def to_number(value: object) -> float:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    if not text:
        return 0
    try:
        return float(text)
    except ValueError:
        return 0


def pick(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if value is None:
            continue
        text = stringify(value, default="")
        if text:
            return text
    return ""
