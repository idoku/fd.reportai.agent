from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"
INPUTS_DIR = ROOT / "inputs"
OUTPUTS_DIR = INPUTS_DIR / "_outputs"
INPUT_JSON_PATH = INPUTS_DIR / "land_cover_input.json"
OUTPUT_MARKDOWN_PATH = OUTPUTS_DIR / "land_valuation_cover.md"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word import WordPipeline  # noqa: E402
from fd_reportai_word.config import ElementValue  # noqa: E402
from fd_reportai_word.context import WordContext  # noqa: E402
from fd_reportai_word.converters import BaseConverter  # noqa: E402


def debug_print(label: str, value: object) -> None:
    print(f"{label}: {value}")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class LandValuationCoverConverter(BaseConverter):
    def convert(self, context: WordContext) -> None:
        print("[converter] start convert")
        debug_print("[converter] detections", context.detections)

        for detection in context.detections:
            if detection.get("key") != "land_valuation_cover":
                continue

            payload = detection.get("payload", {})
            context.elements.update(
                {
                    "report_title": ElementValue(value=payload.get("报告标题", "")),
                    "project_name": ElementValue(value=payload.get("项目名称", "")),
                    "entrusting_party": ElementValue(value=payload.get("委托方", "")),
                    "report_number": ElementValue(value=payload.get("报告编号", "")),
                    "submit_date": ElementValue(value=payload.get("提交日期", "")),
                }
            )
            context.converted_blocks.append(
                {
                    "key": "land_valuation_cover",
                    "type": "cover_page",
                    "content": payload,
                }
            )

        debug_print("[converter] elements", context.elements)
        debug_print("[converter] converted_blocks", context.converted_blocks)
        print("[converter] convert finished")


class TestLandValuationCoverConverter(unittest.TestCase):
    def test_pipeline_reads_land_cover_input_from_path(self) -> None:
        print("\n[test] start test_pipeline_reads_land_cover_input_from_path")

        cover_input = load_json(INPUT_JSON_PATH)
        context = WordContext(
            metadata={"data_snapshot_id": "cover-snapshot-1"},
            detections=[
                {
                    "key": "land_valuation_cover",
                    "payload": cover_input,
                }
            ],
        )
        debug_print("[test] context before run", context)

        pipeline = WordPipeline(converters=[LandValuationCoverConverter()])
        result = pipeline.run(context=context)

        rendered_cover = result.composed_document["sections"][0]["content"]
        rendered_markdown = result.rendered_output["markdown"]

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_MARKDOWN_PATH.write_text(rendered_markdown, encoding="utf-8")

        debug_print("[test] framework", result.framework)
        debug_print("[test] rendered_cover", rendered_cover)
        debug_print("[test] rendered_markdown", rendered_markdown)
        debug_print("[test] output_markdown_path", OUTPUT_MARKDOWN_PATH)
        debug_print("[test] result elements", result.elements)
        debug_print("[test] result converted_blocks", result.converted_blocks)

        self.assertIsNotNone(result.framework)
        self.assertEqual(result.framework.name, "land_conver_v1")
        self.assertEqual(result.composed_document["sections"][0]["key"], "conver")
        self.assertEqual(result.elements["report_title"].value, "土地估价报告")
        self.assertEqual(result.elements["report_number"].value, "湘经估（2025）字第003411A号")
        self.assertEqual(result.converted_blocks[0]["type"], "cover_page")
        self.assertEqual(result.blocked_items, [])
        self.assertEqual(result.validation_errors, [])
        self.assertIn("# 土地估价报告", rendered_cover)
        self.assertIn("项目名称：长沙银行股份有限公司抵押价值评估项目", rendered_cover)
        self.assertIn("委托方：湖南经典房地产评估咨询有限公司", rendered_cover)
        self.assertIn("报告编号：湘经估（2025）字第003411A号", rendered_markdown)
        self.assertIn("## 封面", rendered_markdown)
        self.assertTrue(OUTPUT_MARKDOWN_PATH.exists())
        self.assertEqual(OUTPUT_MARKDOWN_PATH.read_text(encoding="utf-8"), rendered_markdown)

        print("[test] assertions passed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
