from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import json
from typing import Iterable

from ...domain import ValidationIssue
from .computed_fields import LAND_COMPUTED_FIELDS
from .field_registry_data import FIELD_METADATA, LAND_INPUT_PATH, STRUCTURED_COMPUTED_FIELD_LEAVES
from .sections import LAND_SECTIONS


VALID_FIELD_KINDS = {
    "input_block",
    "input_leaf",
    "computed_field",
    "computed_leaf",
    "section_field",
    "static_asset",
}
VALID_FIELD_SHAPES = {
    "scalar",
    "object",
    "array",
    "table",
    "markdown_ref",
    "image_ref",
}
@dataclass(slots=True, frozen=True)
class FieldRegistryEntry:
    key: str
    kind: str
    shape: str
    group: str = "未分组"
    status: str = "active"
    owner: str | None = None
    aliases: tuple[str, ...] = ()
    source_paths: tuple[str, ...] = ()
    leaf_paths: tuple[str, ...] = ()
    derive_from: tuple[str, ...] = ()
    used_by_computed: tuple[str, ...] = ()
    used_by_sections: tuple[str, ...] = ()
    render_to: tuple[str, ...] = ()
    transforms: tuple[str, ...] = ()
    relations: dict[str, tuple[str, ...]] = field(default_factory=dict)
    notes: str | None = None


@dataclass(slots=True)
class _EntryAccumulator:
    key: str
    kind: str
    shape: str
    group: str = "未分组"
    status: str = "active"
    owner: str | None = None
    aliases: set[str] = field(default_factory=set)
    source_paths: set[str] = field(default_factory=set)
    leaf_paths: set[str] = field(default_factory=set)
    derive_from: set[str] = field(default_factory=set)
    used_by_computed: set[str] = field(default_factory=set)
    used_by_sections: set[str] = field(default_factory=set)
    render_to: set[str] = field(default_factory=set)
    transforms: set[str] = field(default_factory=set)
    relations: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    notes: list[str] = field(default_factory=list)

    def freeze(self) -> FieldRegistryEntry:
        notes = tuple(dict.fromkeys(note for note in self.notes if note))
        return FieldRegistryEntry(
            key=self.key,
            kind=self.kind,
            shape=self.shape,
            group=self.group,
            status=self.status,
            owner=self.owner,
            aliases=tuple(sorted(self.aliases)),
            source_paths=tuple(sorted(self.source_paths)),
            leaf_paths=tuple(sorted(self.leaf_paths)),
            derive_from=tuple(sorted(self.derive_from)),
            used_by_computed=tuple(sorted(self.used_by_computed)),
            used_by_sections=tuple(sorted(self.used_by_sections)),
            render_to=tuple(sorted(self.render_to)),
            transforms=tuple(sorted(self.transforms)),
            relations={name: tuple(sorted(values)) for name, values in sorted(self.relations.items()) if values},
            notes="\n".join(notes) if notes else None,
        )


@dataclass(slots=True, frozen=True)
class _ResolvedReference:
    entry_key: str
    token: str


@dataclass(slots=True, frozen=True)
class FieldRegistry:
    entries: dict[str, FieldRegistryEntry]
    alias_index: dict[str, str]
    leaf_path_index: dict[str, str]

    def get(self, key: str) -> FieldRegistryEntry | None:
        return self.entries.get(key)

    def resolve(self, token: str) -> FieldRegistryEntry | None:
        if token in self.entries:
            return self.entries[token]
        alias_key = self.alias_index.get(token)
        if alias_key is None:
            return None
        return self.entries[alias_key]

    def get_by_leaf_path(self, leaf_path: str) -> FieldRegistryEntry | None:
        entry_key = self.leaf_path_index.get(leaf_path)
        if entry_key is None:
            return None
        return self.entries[entry_key]

    def iter_entries(self) -> tuple[FieldRegistryEntry, ...]:
        return tuple(self.entries[key] for key in sorted(self.entries))


def build_land_field_registry() -> FieldRegistry:
    sample = _load_land_input_sample()
    accumulators: dict[str, _EntryAccumulator] = {}
    top_level_leaf_paths: dict[str, set[str]] = defaultdict(set)
    input_leaf_paths_by_key: dict[str, set[str]] = defaultdict(set)
    input_leaf_shapes: dict[str, str] = {}

    _collect_input_shapes(
        value=sample,
        accumulators=accumulators,
        top_level_leaf_paths=top_level_leaf_paths,
        input_leaf_paths_by_key=input_leaf_paths_by_key,
        input_leaf_shapes=input_leaf_shapes,
    )
    _seed_input_blocks(accumulators, sample, top_level_leaf_paths)
    _seed_input_leaves(accumulators, input_leaf_paths_by_key, input_leaf_shapes)
    _seed_computed_fields(accumulators)
    _seed_structured_computed_leaves(accumulators)
    _seed_section_fields(accumulators)

    registry = _freeze_registry(accumulators)
    _populate_computed_relationships(accumulators, registry)
    _populate_section_relationships(accumulators, registry)
    _propagate_leaf_usage(accumulators)
    return _freeze_registry(accumulators)


def validate_land_field_registry() -> list[ValidationIssue]:
    registry = build_land_field_registry()
    issues: list[ValidationIssue] = []
    issues.extend(_validate_entries(registry))
    issues.extend(_validate_computed_field_references(registry))
    issues.extend(_validate_section_references(registry))
    issues.extend(_validate_leaf_coverage(registry))
    issues.extend(_validate_usage(registry))
    return issues


def export_land_field_registry_markdown() -> str:
    registry = build_land_field_registry()
    exposed_entries = [entry for entry in registry.iter_entries() if entry.kind != "input_leaf"]
    input_leaf_entries = [entry for entry in registry.iter_entries() if entry.kind == "input_leaf"]
    lines = [
        "# 土地报告字段注册表",
        "",
        "## Summary",
        "",
        f"- 字段总数：{len(registry.entries)}",
        f"- 暴露字段数：{len(exposed_entries)}",
        f"- 原始输入叶子字段数：{len(input_leaf_entries)}",
        "",
        "## 暴露字段总表",
        "",
        "| 字段 | 分组 | 类型 | 形状 | 来源 | 派生依赖 | 章节去向 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in exposed_entries:
        lines.append(
            "| {key} | {group} | {kind} | {shape} | {source} | {derive} | {render} |".format(
                key=entry.key,
                group=entry.group,
                kind=entry.kind,
                shape=entry.shape,
                source=_inline_list(entry.source_paths),
                derive=_inline_list(entry.derive_from),
                render=_inline_list(entry.render_to),
            )
        )

    lines.extend(
        [
            "",
            "## 字段详情",
            "",
        ]
    )
    for entry in exposed_entries:
        lines.extend(
            [
                f"### {entry.key}",
                "",
                f"- 类型：`{entry.kind}`",
                f"- 形状：`{entry.shape}`",
                f"- 分组：`{entry.group}`",
                f"- 状态：`{entry.status}`",
                f"- 负责人：{entry.owner if entry.owner else '未指定'}",
                f"- 来源：{_bullet_value(entry.source_paths)}",
                f"- 叶子路径：{_bullet_value(entry.leaf_paths)}",
                f"- 派生依赖：{_bullet_value(entry.derive_from)}",
                f"- 被计算字段使用：{_bullet_value(entry.used_by_computed)}",
                f"- 被章节消费：{_bullet_value(entry.used_by_sections)}",
                f"- 渲染去向：{_bullet_value(entry.render_to)}",
                f"- 变换：{_bullet_value(entry.transforms)}",
                f"- 别名：{_bullet_value(entry.aliases)}",
                f"- 关系：{_format_relations(entry.relations)}",
                f"- 备注：{entry.notes if entry.notes else '无'}",
                "",
            ]
        )

    lines.extend(
        [
            "## 原始输入叶子路径表",
            "",
            "| 叶子字段 | 路径 | 形状 | 归属 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for entry in input_leaf_entries:
        parent_keys = entry.relations.get("input_blocks", ())
        for leaf_path in entry.leaf_paths:
            lines.append(
                f"| {entry.key} | {leaf_path} | {entry.shape} | {_inline_list(parent_keys) or '无'} |"
            )

    lines.extend(
        [
            "",
            "## 血缘视图",
            "",
        ]
    )
    lineage_rows = _build_lineage_rows(registry)
    for source_key, computed_targets, section_targets in lineage_rows:
        lines.append(f"### {source_key}")
        lines.append("")
        lines.append(f"- 流向计算字段：{_bullet_value(computed_targets)}")
        lines.append(f"- 流向章节：{_bullet_value(section_targets)}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _load_land_input_sample() -> dict[str, object]:
    return json.loads(LAND_INPUT_PATH.read_text(encoding="utf-8"))


def _collect_input_shapes(
    *,
    value: object,
    accumulators: dict[str, _EntryAccumulator],
    top_level_leaf_paths: dict[str, set[str]],
    input_leaf_paths_by_key: dict[str, set[str]],
    input_leaf_shapes: dict[str, str],
) -> None:
    if not isinstance(value, dict):
        return
    for top_level_key, top_level_value in value.items():
        _walk_input_value(
            value=top_level_value,
            path=[top_level_key],
            top_level_key=top_level_key,
            top_level_leaf_paths=top_level_leaf_paths,
            input_leaf_paths_by_key=input_leaf_paths_by_key,
            input_leaf_shapes=input_leaf_shapes,
        )
        accumulators.setdefault(
            top_level_key,
            _EntryAccumulator(
                key=top_level_key,
                kind="input_block",
                shape=_infer_shape(top_level_value),
            ),
        )


def _walk_input_value(
    *,
    value: object,
    path: list[str],
    top_level_key: str,
    top_level_leaf_paths: dict[str, set[str]],
    input_leaf_paths_by_key: dict[str, set[str]],
    input_leaf_shapes: dict[str, str],
) -> None:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            _walk_input_value(
                value=child_value,
                path=[*path, child_key],
                top_level_key=top_level_key,
                top_level_leaf_paths=top_level_leaf_paths,
                input_leaf_paths_by_key=input_leaf_paths_by_key,
                input_leaf_shapes=input_leaf_shapes,
            )
        return

    if isinstance(value, list):
        list_path = path[:-1] + [path[-1] + "[]"]
        if not value:
            leaf_path = ".".join(list_path)
            top_level_leaf_paths[top_level_key].add(leaf_path)
            input_leaf_paths_by_key[path[-1]].add(leaf_path)
            input_leaf_shapes[path[-1]] = _merge_shape(input_leaf_shapes.get(path[-1]), "array")
            return
        if all(not isinstance(item, (dict, list)) for item in value):
            leaf_path = ".".join(list_path)
            top_level_leaf_paths[top_level_key].add(leaf_path)
            input_leaf_paths_by_key[path[-1]].add(leaf_path)
            input_leaf_shapes[path[-1]] = _merge_shape(input_leaf_shapes.get(path[-1]), _infer_shape(value))
            return
        for item in value:
            _walk_input_value(
                value=item,
                path=list_path,
                top_level_key=top_level_key,
                top_level_leaf_paths=top_level_leaf_paths,
                input_leaf_paths_by_key=input_leaf_paths_by_key,
                input_leaf_shapes=input_leaf_shapes,
            )
        return

    leaf_key = path[-1].replace("[]", "")
    leaf_path = ".".join(path)
    top_level_leaf_paths[top_level_key].add(leaf_path)
    input_leaf_paths_by_key[leaf_key].add(leaf_path)
    input_leaf_shapes[leaf_key] = _merge_shape(input_leaf_shapes.get(leaf_key), _infer_shape(value))


def _seed_input_blocks(
    accumulators: dict[str, _EntryAccumulator],
    sample: dict[str, object],
    top_level_leaf_paths: dict[str, set[str]],
) -> None:
    for key, value in sample.items():
        entry = accumulators[key]
        entry.kind = "input_block"
        entry.shape = _infer_shape(value)
        _apply_field_metadata(entry)
        entry.source_paths.add(key)
        entry.leaf_paths.update(top_level_leaf_paths.get(key, set()))
        for leaf_path in top_level_leaf_paths.get(key, set()):
            entry.relations["leaf_paths"].add(leaf_path)


def _seed_input_leaves(
    accumulators: dict[str, _EntryAccumulator],
    input_leaf_paths_by_key: dict[str, set[str]],
    input_leaf_shapes: dict[str, str],
) -> None:
    for key, leaf_paths in input_leaf_paths_by_key.items():
        entry = accumulators.setdefault(
            key,
            _EntryAccumulator(
                key=key,
                kind="input_leaf",
                shape=input_leaf_shapes.get(key, "scalar"),
            ),
        )
        if entry.kind == "section_field":
            continue
        if entry.kind != "input_block":
            entry.kind = "input_leaf"
        entry.shape = input_leaf_shapes.get(key, entry.shape)
        _apply_field_metadata(entry)
        entry.source_paths.update(leaf_paths)
        entry.leaf_paths.update(leaf_paths)
        for leaf_path in leaf_paths:
            parent_key = leaf_path.split(".", 1)[0].replace("[]", "")
            entry.relations["input_blocks"].add(parent_key)


def _seed_computed_fields(accumulators: dict[str, _EntryAccumulator]) -> None:
    for computed_field in LAND_COMPUTED_FIELDS:
        shape = _shape_for_computed_field(computed_field.mode, computed_field.options)
        entry = accumulators.setdefault(
            computed_field.key,
            _EntryAccumulator(
                key=computed_field.key,
                kind="computed_field",
                shape=shape,
            ),
        )
        entry.kind = "computed_field"
        entry.shape = shape
        _apply_field_metadata(entry)
        entry.source_paths.add(computed_field.key)
        entry.notes.append(f"mode={computed_field.mode}")


def _seed_structured_computed_leaves(accumulators: dict[str, _EntryAccumulator]) -> None:
    for parent_key, children in STRUCTURED_COMPUTED_FIELD_LEAVES.items():
        parent_entry = accumulators[parent_key]
        for child_key, shape in children:
            entry = accumulators.setdefault(
                child_key,
                _EntryAccumulator(
                    key=child_key,
                    kind="computed_leaf",
                    shape=shape,
                ),
            )
            entry.kind = "computed_leaf"
            entry.shape = shape
            _apply_field_metadata(entry)
            computed_path = f"{parent_key}.{child_key}"
            entry.source_paths.add(computed_path)
            entry.leaf_paths.add(computed_path)
            entry.derive_from.add(parent_key)
            entry.relations["computed_parent"].add(parent_key)
            parent_entry.leaf_paths.add(computed_path)
            parent_entry.relations["computed_leaves"].add(child_key)


def _seed_section_fields(accumulators: dict[str, _EntryAccumulator]) -> None:
    for section_ref in _iter_section_definitions():
        key = section_ref["definition"].key
        if key in accumulators:
            continue
        source_token = section_ref["definition"].source_key or key
        source_entry = accumulators.get(source_token)
        shape = source_entry.shape if source_entry is not None else _infer_shape(section_ref["definition"].default_value)
        if shape not in VALID_FIELD_SHAPES:
            shape = "scalar"
        entry = accumulators[key] = _EntryAccumulator(key=key, kind="section_field", shape=shape)
        _apply_field_metadata(entry)
        entry.source_paths.add(source_token)
        if section_ref["definition"].default_value is not None:
            entry.notes.append("来自章节默认值或模板占位。")

def _freeze_registry(accumulators: dict[str, _EntryAccumulator]) -> FieldRegistry:
    entries = {key: accumulator.freeze() for key, accumulator in sorted(accumulators.items())}
    alias_index: dict[str, str] = {}
    for entry in entries.values():
        for alias in entry.aliases:
            if alias in entries:
                continue
            alias_index[alias] = entry.key
    leaf_path_index: dict[str, str] = {}
    for entry in sorted(entries.values(), key=lambda item: _leaf_path_priority(item.kind), reverse=True):
        for leaf_path in entry.leaf_paths:
            leaf_path_index.setdefault(leaf_path, entry.key)
    return FieldRegistry(entries=entries, alias_index=alias_index, leaf_path_index=leaf_path_index)


def _populate_computed_relationships(
    accumulators: dict[str, _EntryAccumulator],
    registry: FieldRegistry,
) -> None:
    for computed_field in LAND_COMPUTED_FIELDS:
        entry = accumulators[computed_field.key]
        for definition in computed_field.input_blocks:
            resolved = _resolve_reference(definition.source_key or definition.key, registry)
            if resolved is None:
                continue
            entry.derive_from.add(resolved.entry_key)
            entry.relations["input_blocks"].add(definition.key)
            accumulators[resolved.entry_key].used_by_computed.add(computed_field.key)


def _populate_section_relationships(
    accumulators: dict[str, _EntryAccumulator],
    registry: FieldRegistry,
) -> None:
    for section_ref in _iter_section_definitions():
        definition = section_ref["definition"]
        target_key = definition.key
        target_entry = accumulators[target_key]
        render_target = _render_target(section_ref)
        target_entry.used_by_sections.add(render_target)
        target_entry.render_to.add(render_target)
        transform = definition.options.get("transform")
        if isinstance(transform, str):
            target_entry.transforms.add(transform)

        source_reference = _resolve_preferred_source(definition, registry)
        if source_reference is None:
            continue
        source_entry = accumulators[source_reference.entry_key]
        source_entry.used_by_sections.add(render_target)
        source_entry.render_to.add(render_target)
        if isinstance(transform, str):
            source_entry.transforms.add(transform)
        if source_reference.entry_key != target_key:
            target_entry.derive_from.add(source_reference.entry_key)
            target_entry.relations["mapped_from"].add(source_reference.entry_key)
            source_entry.relations["mapped_to"].add(target_key)


def _propagate_leaf_usage(accumulators: dict[str, _EntryAccumulator]) -> None:
    for entry in accumulators.values():
        if entry.kind != "input_leaf":
            continue
        parent_blocks = entry.relations.get("input_blocks", set())
        for parent_key in parent_blocks:
            parent_entry = accumulators.get(parent_key)
            if parent_entry is None:
                continue
            entry.used_by_computed.update(parent_entry.used_by_computed)
            entry.used_by_sections.update(parent_entry.used_by_sections)
            entry.render_to.update(parent_entry.render_to)
            parent_entry.used_by_computed.update(entry.used_by_computed)
            parent_entry.used_by_sections.update(entry.used_by_sections)
            parent_entry.render_to.update(entry.render_to)


def _validate_entries(registry: FieldRegistry) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for entry in registry.entries.values():
        if entry.kind not in VALID_FIELD_KINDS:
            issues.append(
                ValidationIssue(
                    code="invalid_kind",
                    message=f"字段 {entry.key} 使用了非法 kind: {entry.kind}",
                )
            )
        if entry.shape not in VALID_FIELD_SHAPES:
            issues.append(
                ValidationIssue(
                    code="invalid_shape",
                    message=f"字段 {entry.key} 使用了非法 shape: {entry.shape}",
                )
            )
    alias_targets: dict[str, list[str]] = defaultdict(list)
    for entry in registry.entries.values():
        for alias in entry.aliases:
            alias_targets[alias].append(entry.key)
    for alias, keys in alias_targets.items():
        if len(keys) > 1:
            issues.append(
                ValidationIssue(
                    code="duplicate_alias",
                    message=f"别名 {alias} 同时指向多个字段: {', '.join(sorted(keys))}",
                )
            )
    issues.extend(_validate_derive_cycles(registry))
    issues.extend(_validate_relation_references(registry))
    return issues


def _validate_computed_field_references(registry: FieldRegistry) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for computed_field in LAND_COMPUTED_FIELDS:
        entry = registry.get(computed_field.key)
        if entry is None or entry.kind != "computed_field":
            issues.append(
                ValidationIssue(
                    code="missing_computed_field",
                    message=f"计算字段 {computed_field.key} 未注册或 kind 不为 computed_field。",
                )
            )
        for definition in computed_field.input_blocks:
            issues.extend(_validate_definition_tokens(definition, registry, scope=f"computed:{computed_field.key}"))
    return issues


def _validate_section_references(registry: FieldRegistry) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for section_ref in _iter_section_definitions():
        definition = section_ref["definition"]
        issues.extend(_validate_definition_tokens(definition, registry, scope=_render_target(section_ref)))
    return issues


def _validate_leaf_coverage(registry: FieldRegistry) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    sample = _load_land_input_sample()
    expected_leaf_paths = _collect_all_leaf_paths(sample)
    for leaf_path in sorted(expected_leaf_paths):
        if registry.get_by_leaf_path(leaf_path) is None:
            issues.append(
                ValidationIssue(
                    code="missing_leaf_path",
                    message=f"叶子路径未注册: {leaf_path}",
                )
            )
    for entry in registry.entries.values():
        if entry.shape not in {"object", "array"}:
            continue
        if entry.kind not in {"input_block", "computed_field"}:
            continue
        if not entry.leaf_paths:
            issues.append(
                ValidationIssue(
                    code="missing_leaf_coverage",
                    message=f"字段 {entry.key} 为 {entry.shape}，但未登记叶子路径。",
                )
            )
    for entry in registry.entries.values():
        for leaf_path in entry.leaf_paths:
            if entry.kind == "input_block":
                continue
            if registry.get_by_leaf_path(leaf_path) is None:
                issues.append(
                    ValidationIssue(
                        code="orphan_leaf_path",
                        message=f"字段 {entry.key} 记录了未索引的叶子路径: {leaf_path}",
                    )
                )
    return issues


def _validate_usage(registry: FieldRegistry) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for entry in registry.entries.values():
        if entry.status in {"reserved", "deprecated"}:
            continue
        if _is_effectively_used(entry):
            continue
        issues.append(
            ValidationIssue(
                code="unused_field",
                message=f"字段 {entry.key} 未被任何规则消费。",
                severity="warning",
            )
        )
    return issues


def _validate_derive_cycles(registry: FieldRegistry) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    permanent: set[str] = set()
    temporary: set[str] = set()

    def visit(key: str, stack: list[str]) -> None:
        if key in permanent:
            return
        if key in temporary:
            cycle = " -> ".join([*stack, key])
            issues.append(
                ValidationIssue(
                    code="derive_cycle",
                    message=f"字段派生关系存在循环: {cycle}",
                )
            )
            return
        temporary.add(key)
        stack.append(key)
        entry = registry.entries.get(key)
        if entry is not None:
            for dependency in entry.derive_from:
                if dependency in registry.entries:
                    visit(dependency, stack)
        stack.pop()
        temporary.remove(key)
        permanent.add(key)

    for key in sorted(registry.entries):
        visit(key, [])
    return issues


def _validate_relation_references(registry: FieldRegistry) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for entry in registry.entries.values():
        for relation_name, relation_values in entry.relations.items():
            for relation_value in relation_values:
                if relation_name in {"leaf_paths"}:
                    continue
                if relation_name == "input_blocks" and relation_value in registry.entries:
                    continue
                if relation_value in registry.entries:
                    continue
                if relation_value in registry.alias_index:
                    continue
                issues.append(
                    ValidationIssue(
                        code="orphan_relation",
                        message=f"字段 {entry.key} 的关系 {relation_name} 指向不存在的字段: {relation_value}",
                    )
                )
    return issues


def _validate_definition_tokens(definition, registry: FieldRegistry, *, scope: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    tokens = [("key", definition.key)]
    if definition.source_key is not None:
        tokens.append(("source_key", definition.source_key))
    tokens.extend(("alias", alias) for alias in definition.aliases)
    for token_type, token in tokens:
        if registry.resolve(token) is None:
            issues.append(
                ValidationIssue(
                    code="unresolved_reference",
                    message=f"{scope} 中的 {token_type}={token} 无法解析到注册字段。",
                )
            )
    return issues


def _collect_all_leaf_paths(sample: dict[str, object]) -> set[str]:
    leaf_paths: set[str] = set()

    def walk(value: object, path: list[str]) -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                walk(child_value, [*path, child_key])
            return
        if isinstance(value, list):
            list_path = path[:-1] + [path[-1] + "[]"]
            if not value or all(not isinstance(item, (dict, list)) for item in value):
                leaf_paths.add(".".join(list_path))
                return
            for item in value:
                walk(item, list_path)
            return
        leaf_paths.add(".".join(path))

    walk(sample, [])
    return leaf_paths


def _resolve_reference(token: str, registry: FieldRegistry) -> _ResolvedReference | None:
    entry = registry.resolve(token)
    if entry is None:
        return None
    return _ResolvedReference(entry_key=entry.key, token=token)


def _resolve_preferred_source(definition, registry: FieldRegistry) -> _ResolvedReference | None:
    candidate_tokens = [definition.source_key or definition.key, *definition.aliases]
    for token in candidate_tokens:
        resolved = _resolve_reference(token, registry)
        if resolved is None:
            continue
        entry = registry.entries[resolved.entry_key]
        if resolved.entry_key != definition.key or entry.kind != "section_field":
            return resolved
    for token in candidate_tokens:
        resolved = _resolve_reference(token, registry)
        if resolved is not None:
            return resolved
    return None


def _iter_section_definitions() -> tuple[dict[str, object], ...]:
    definitions: list[dict[str, object]] = []
    for section in LAND_SECTIONS:
        for definition in section.elements:
            definitions.append(
                {
                    "section_key": section.key,
                    "section_title": section.title,
                    "content_item_key": None,
                    "definition": definition,
                }
            )
        for content_item in section.content_items:
            for definition in content_item.elements:
                definitions.append(
                    {
                        "section_key": section.key,
                        "section_title": section.title,
                        "content_item_key": content_item.key,
                        "definition": definition,
                    }
                )
    return tuple(definitions)


def _render_target(section_ref: dict[str, object]) -> str:
    content_item_key = section_ref["content_item_key"]
    if content_item_key:
        return f"{section_ref['section_key']}/{content_item_key}/{section_ref['definition'].key}"
    return f"{section_ref['section_key']}/{section_ref['definition'].key}"


def _shape_for_computed_field(mode: str, options: dict[str, object]) -> str:
    if mode == "llm_json":
        return "object"
    if mode in {"llm_table"} or options.get("transform") == "land_result_table":
        return "table"
    return "scalar"


def _infer_shape(value: object) -> str:
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, str):
        if value.endswith(".md"):
            return "markdown_ref"
        if value.endswith((".png", ".jpg", ".jpeg", ".webp")):
            return "image_ref"
    return "scalar"


def _merge_shape(existing: str | None, current: str) -> str:
    if existing is None or existing == current:
        return current
    priorities = {
        "image_ref": 5,
        "markdown_ref": 4,
        "table": 3,
        "array": 2,
        "object": 1,
        "scalar": 0,
    }
    return current if priorities[current] >= priorities.get(existing, 0) else existing


def _leaf_path_priority(kind: str) -> int:
    priorities = {
        "computed_leaf": 5,
        "input_leaf": 4,
        "section_field": 3,
        "computed_field": 2,
        "input_block": 1,
        "static_asset": 0,
    }
    return priorities.get(kind, 0)


def _is_effectively_used(entry: FieldRegistryEntry) -> bool:
    return bool(entry.used_by_computed or entry.used_by_sections or entry.render_to)


def _apply_field_metadata(entry: _EntryAccumulator) -> None:
    metadata = FIELD_METADATA.get(entry.key)
    if metadata is None:
        return
    entry.group = metadata.group
    entry.status = metadata.status
    entry.owner = metadata.owner
    entry.aliases.update(metadata.aliases)
    entry.notes.extend(metadata.notes)
    for relation_name, values in metadata.relations.items():
        entry.relations[relation_name].update(values)
    # propagate new metadata fields
    if metadata.source:
        entry.source_paths.add(metadata.source)
    if metadata.feeds_into:
        entry.relations["feeds_into"].update(metadata.feeds_into)


def _inline_list(values: Iterable[str]) -> str:
    return ", ".join(values)


def _bullet_value(values: Iterable[str]) -> str:
    items = list(values)
    if not items:
        return "无"
    return "；".join(items)


def _format_relations(relations: dict[str, tuple[str, ...]]) -> str:
    if not relations:
        return "无"
    parts = [f"{name}={_inline_list(values)}" for name, values in relations.items()]
    return "；".join(parts)


def _build_lineage_rows(registry: FieldRegistry) -> list[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    rows: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []
    for entry in registry.iter_entries():
        if not _is_effectively_used(entry):
            continue
        rows.append(
            (
                entry.key,
                entry.used_by_computed,
                entry.render_to,
            )
        )
    return rows
