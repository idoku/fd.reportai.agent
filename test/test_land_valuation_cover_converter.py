from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"
INPUTS_DIR = ROOT / "inputs"
OUTPUTS_DIR = INPUTS_DIR / "_outputs"
INPUT_JSON_PATH = INPUTS_DIR / "land_cover_input.json"
OUTPUT_MARKDOWN_PATH = OUTPUTS_DIR / "land_valuation_cover.md"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word import WordPipeline, get_default_ruleset  # noqa: E402
from fd_reportai_word.context import WordContext  # noqa: E402
from fd_reportai_word.converters import LandValuationCoverConverter  # noqa: E402


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class TestLandValuationCoverConverter(unittest.TestCase):
    def test_pipeline_reads_land_cover_input_from_path(self) -> None:
        cover_input = load_json(INPUT_JSON_PATH)
        context = WordContext(
            framework=get_default_ruleset("land_conver"),
            metadata={"data_snapshot_id": "cover-snapshot-1"},
            detections=[
                {
                    "key": "land_valuation_cover",
                    "payload": cover_input,
                }
            ],
        )

        result = WordPipeline(converters=[LandValuationCoverConverter()]).run(context=context)

        rendered_cover = result.composed_document["sections"][0]["content"]
        rendered_markdown = result.rendered_output["markdown"]

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_MARKDOWN_PATH.write_text(rendered_markdown, encoding="utf-8")

        self.assertIsNotNone(result.framework)
        self.assertEqual(result.framework.name, "land_conver_v1")
        self.assertEqual(result.composed_document["sections"][0]["key"], "conver")
        self.assertEqual(result.converted_blocks[0]["type"], "cover_page")
        self.assertEqual(result.blocked_items, [])
        self.assertEqual(result.validation_errors, [])
        self.assertTrue(result.elements["report_title"].value)
        self.assertTrue(result.elements["report_number"].value)
        self.assertIn(str(result.elements["project_name"].value), rendered_cover)
        self.assertIn(str(result.elements["entrusting_party"].value), rendered_cover)
        self.assertIn(str(result.elements["report_number"].value), rendered_markdown)
        self.assertIn(result.framework.title, rendered_markdown)
        self.assertTrue(OUTPUT_MARKDOWN_PATH.exists())
        self.assertEqual(OUTPUT_MARKDOWN_PATH.read_text(encoding="utf-8"), rendered_markdown)


if __name__ == "__main__":
    unittest.main(verbosity=2)
