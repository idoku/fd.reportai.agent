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
OUTPUT_MARKDOWN_PATH = OUTPUTS_DIR / "land_cover.md"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word import LLMLocator, WordPipeline, get_default_ruleset  # noqa: E402
from fd_reportai_word.llm.config import env_str, load_dotenv_if_available  # noqa: E402


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class TestLandCoverPipeline(unittest.TestCase):
    def test_pipeline_renders_land_cover_with_doubao(self) -> None:
        load_dotenv_if_available(ROOT)
        elements = load_json(INPUT_JSON_PATH)
        locator = LLMLocator(
            provider="doubao",
            model=env_str("DOUBAO_MODEL_NAME"),
            api_key=env_str("DOUBAO_MODEL_KEY"),
            base_url=env_str("DOUBAO_MODEL_URL"),
        )

        result = WordPipeline(locator=locator).run(
            framework=get_default_ruleset("ruleset_land"),
            elements=elements,
            metadata={"data_snapshot_id": "cover-snapshot-1"},
        )

        cover_block = result.block_results[0]
        cover_text = cover_block.content["text"]
        rendered_markdown = result.rendered_output["markdown"]

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_MARKDOWN_PATH.write_text(rendered_markdown, encoding="utf-8")

        self.assertIsNotNone(result.framework)
        self.assertEqual(result.framework.name, "ruleset_land_v1")
        self.assertEqual(len(result.block_results), 1)
        self.assertEqual(cover_block.block_key, "cover")
        self.assertEqual(cover_block.generator_mode, "template")
        self.assertEqual(result.blocked_items, [])
        self.assertEqual(result.validation_errors, [])
        self.assertEqual(cover_block.trace.data_snapshot_id, "cover-snapshot-1")
        self.assertIn("# 土地估价报告", cover_text)
        self.assertIn("项目名称：长沙银行股份有限公司抵押价值评估项目", cover_text)
        self.assertIn("委托方：湖南经典房地产评估咨询有限公司", cover_text)
        self.assertIn("报告编号：湘经评估（2025）字第03411A号", cover_text)
        self.assertIn("提交日期：二〇二五年十二月十六日", cover_text)
        self.assertIn("# 土地估价报告", rendered_markdown)
        self.assertIn("## 封面", rendered_markdown)
        self.assertIn("项目名称：长沙银行股份有限公司抵押价值评估项目", rendered_markdown)
        self.assertIn("委托方：湖南经典房地产评估咨询有限公司", rendered_markdown)
        self.assertTrue(OUTPUT_MARKDOWN_PATH.exists())
        self.assertEqual(OUTPUT_MARKDOWN_PATH.read_text(encoding="utf-8"), rendered_markdown)


if __name__ == "__main__":
    unittest.main(verbosity=2)
