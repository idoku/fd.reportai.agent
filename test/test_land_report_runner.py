from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"
INPUT_PATH = ROOT / "inputs" / "land_input.json"
OUTPUT_PATH = ROOT / "inputs" / "_outputs" / "land_report_cover.md"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word import GLOBAL_LLM_REGISTRY, LLMLocator, LandReportRunner  # noqa: E402
from fd_reportai_word.land_blocks import LAND_BLOCKS  # noqa: E402


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class TestLandReportRunner(unittest.TestCase):
    def test_registry_contains_expected_providers(self) -> None:
        providers = set(GLOBAL_LLM_REGISTRY.providers())
        self.assertTrue({"mock", "local", "qwen", "doubao", "kimi"}.issubset(providers))

    def test_runner_builds_cover_from_land_input(self) -> None:
        payload = load_json(INPUT_PATH)
        cover_block = LAND_BLOCKS["cover"]

        artifacts = LandReportRunner(locator=LLMLocator(provider="mock")).run_from_file(
            INPUT_PATH,
            output_path=OUTPUT_PATH,
        )

        self.assertEqual(len(artifacts.block_results), 1)

        block = artifacts.block_results[0]
        markdown = artifacts.markdown

        self.assertEqual(block.block_key, cover_block.key)
        self.assertEqual(block.title, cover_block.title)
        self.assertEqual(set(block.selected_input.keys()), set(cover_block.input_keys))
        self.assertEqual(block.selected_input, {key: payload[key] for key in cover_block.input_keys})
        self.assertEqual(set(block.generated_fields.keys()), set(cover_block.output_fields))
        self.assertEqual(block.provider, "mock")
        self.assertIsNotNone(block.model)
        self.assertTrue(block.prompt_preview)
        self.assertTrue(block.rendered_content)
        self.assertIn(f"## {cover_block.title}", markdown)
        self.assertIn(block.rendered_content, markdown)
        self.assertTrue(OUTPUT_PATH.exists())
        self.assertEqual(OUTPUT_PATH.read_text(encoding="utf-8"), markdown)


if __name__ == "__main__":
    unittest.main(verbosity=2)
