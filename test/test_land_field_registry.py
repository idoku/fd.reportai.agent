from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"
DOC_PATH = ROOT / "docs" / "land_field_registry.md"
INPUT_PATH = ROOT / "inputs" / "land_input.json"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word.rules.land import (  # noqa: E402
    build_land_field_registry,
    export_land_field_registry_markdown,
    field_registry_cli_main,
    validate_land_field_registry,
)


def _load_land_input() -> dict[str, object]:
    return json.loads(INPUT_PATH.read_text(encoding="utf-8"))


def _collect_leaf_paths(value: object, path: list[str] | None = None) -> set[str]:
    current_path = list(path or [])
    leaf_paths: set[str] = set()
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            leaf_paths.update(_collect_leaf_paths(child_value, [*current_path, child_key]))
        return leaf_paths
    if isinstance(value, list):
        list_path = current_path[:-1] + [current_path[-1] + "[]"]
        if not value or all(not isinstance(item, (dict, list)) for item in value):
            leaf_paths.add(".".join(list_path))
            return leaf_paths
        for item in value:
            leaf_paths.update(_collect_leaf_paths(item, list_path))
        return leaf_paths
    leaf_paths.add(".".join(current_path))
    return leaf_paths


class TestLandFieldRegistry(unittest.TestCase):
    def test_registry_has_no_validation_issues(self) -> None:
        self.assertEqual(validate_land_field_registry(), [])

    def test_registry_covers_representative_fields(self) -> None:
        registry = build_land_field_registry()
        self.assertEqual(registry.get("地价定义分项设定").kind, "computed_field")
        self.assertEqual(registry.get("地价定义分项设定").shape, "object")
        self.assertEqual(registry.get("用途设定").kind, "computed_leaf")
        self.assertEqual(registry.get("委托方").kind, "section_field")
        self.assertEqual(registry.get("项目信息").kind, "input_block")
        self.assertIsNotNone(registry.resolve("法定代表人签字"))

    def test_registry_covers_all_input_leaf_paths(self) -> None:
        registry = build_land_field_registry()
        expected_leaf_paths = _collect_leaf_paths(_load_land_input())
        self.assertTrue(expected_leaf_paths)
        for leaf_path in sorted(expected_leaf_paths):
            entry = registry.get_by_leaf_path(leaf_path)
            self.assertIsNotNone(entry, leaf_path)

    def test_registry_export_matches_docs_snapshot(self) -> None:
        exported = export_land_field_registry_markdown()
        self.assertIn("## 暴露字段总表", exported)
        self.assertIn("## 原始输入叶子路径表", exported)
        self.assertIn("## 血缘视图", exported)
        self.assertEqual(DOC_PATH.read_text(encoding="utf-8"), exported)

    def test_cli_show_and_validate(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = field_registry_cli_main(["show", "地价定义分项设定"])
        self.assertEqual(exit_code, 0)
        self.assertIn("字段: 地价定义分项设定", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = field_registry_cli_main(["validate"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue().strip(), "OK")

    def test_cli_export_doc(self) -> None:
        temp_dir = ROOT / "inputs" / "_outputs" / "registry_test"
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_path = temp_dir / "registry.md"
        try:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = field_registry_cli_main(["export-doc", "--output", str(output_path)])
            self.assertEqual(exit_code, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), export_land_field_registry_markdown())
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main(verbosity=2)
