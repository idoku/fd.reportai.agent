from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .field_registry import (
    FieldRegistryEntry,
    build_land_field_registry,
    export_land_field_registry_markdown,
    validate_land_field_registry,
)


DEFAULT_DOC_PATH = Path(__file__).resolve().parents[6] / "docs" / "land_field_registry.md"


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        return _cmd_list(group=args.group, kind=args.kind)
    if args.command == "show":
        return _cmd_show(args.key)
    if args.command == "lineage":
        return _cmd_lineage(args.key)
    if args.command == "validate":
        return _cmd_validate()
    if args.command == "export-doc":
        return _cmd_export_doc(Path(args.output))
    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="土地报告字段注册表管理工具")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="列出字段")
    list_parser.add_argument("--group", help="按分组过滤")
    list_parser.add_argument("--kind", help="按类型过滤")

    show_parser = subparsers.add_parser("show", help="查看单个字段详情")
    show_parser.add_argument("key", help="字段 key 或 alias")

    lineage_parser = subparsers.add_parser("lineage", help="查看字段血缘")
    lineage_parser.add_argument("key", help="字段 key 或 alias")

    subparsers.add_parser("validate", help="运行字段注册表校验")

    export_parser = subparsers.add_parser("export-doc", help="导出 Markdown 文档")
    export_parser.add_argument("--output", default=str(DEFAULT_DOC_PATH), help="输出路径")
    return parser


def _cmd_list(*, group: str | None, kind: str | None) -> int:
    registry = build_land_field_registry()
    entries = []
    for entry in registry.iter_entries():
        if group and entry.group != group:
            continue
        if kind and entry.kind != kind:
            continue
        entries.append(entry)
    for entry in entries:
        print(f"{entry.key}\t{entry.group}\t{entry.kind}\t{entry.shape}")
    return 0


def _cmd_show(token: str) -> int:
    registry = build_land_field_registry()
    entry = registry.resolve(token)
    if entry is None:
        print(f"未找到字段: {token}", file=sys.stderr)
        return 1
    print(_format_entry(entry))
    return 0


def _cmd_lineage(token: str) -> int:
    registry = build_land_field_registry()
    entry = registry.resolve(token)
    if entry is None:
        print(f"未找到字段: {token}", file=sys.stderr)
        return 1
    print(f"字段: {entry.key}")
    print(f"分组: {entry.group}")
    print(f"派生依赖: {_join(entry.derive_from)}")
    print(f"被计算字段使用: {_join(entry.used_by_computed)}")
    print(f"被章节消费: {_join(entry.used_by_sections)}")
    print(f"渲染去向: {_join(entry.render_to)}")
    return 0


def _cmd_validate() -> int:
    issues = validate_land_field_registry()
    if not issues:
        print("OK")
        return 0
    for issue in issues:
        print(f"{issue.severity}\t{issue.code}\t{issue.message}")
    return 1


def _cmd_export_doc(output_path: Path) -> int:
    output_path.write_text(export_land_field_registry_markdown(), encoding="utf-8")
    print(output_path)
    return 0


def _format_entry(entry: FieldRegistryEntry) -> str:
    return "\n".join(
        [
            f"字段: {entry.key}",
            f"分组: {entry.group}",
            f"类型: {entry.kind}",
            f"形状: {entry.shape}",
            f"状态: {entry.status}",
            f"负责人: {entry.owner or '未指定'}",
            f"来源: {_join(entry.source_paths)}",
            f"叶子路径: {_join(entry.leaf_paths)}",
            f"派生依赖: {_join(entry.derive_from)}",
            f"被计算字段使用: {_join(entry.used_by_computed)}",
            f"被章节消费: {_join(entry.used_by_sections)}",
            f"渲染去向: {_join(entry.render_to)}",
            f"变换: {_join(entry.transforms)}",
            f"别名: {_join(entry.aliases)}",
            f"关系: {_format_relations(entry.relations)}",
            f"备注: {entry.notes or '无'}",
        ]
    )


def _format_relations(relations: dict[str, tuple[str, ...]]) -> str:
    if not relations:
        return "无"
    return "；".join(f"{name}={_join(values)}" for name, values in sorted(relations.items()))


def _join(values: tuple[str, ...]) -> str:
    return "；".join(values) if values else "无"


if __name__ == "__main__":
    raise SystemExit(main())
