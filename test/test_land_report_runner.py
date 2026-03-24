from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"
INPUT_PATH = ROOT / "inputs" / "lnad_input.json"
OUTPUT_PATH = ROOT / "inputs" / "_outputs" / "lnad_report.md"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word import GLOBAL_LLM_REGISTRY, LLMLocator, LandReportRunner  # noqa: E402


class TestLandReportRunner(unittest.TestCase):
    def test_runner_reads_unified_input_and_generates_markdown(self) -> None:
        artifacts = LandReportRunner(locator=LLMLocator(provider="mock")).run_from_file(
            INPUT_PATH,
            output_path=OUTPUT_PATH,
        )

        markdown = artifacts.context.rendered_output["markdown"]

        self.assertIn("## 封面", markdown)
        self.assertIn("## 摘要", markdown)
        self.assertIn("[MOCK:langchain]", markdown)
        self.assertIn("项目名称：长沙银行股份有限公司抵押价值评估项目", markdown)
        self.assertTrue(OUTPUT_PATH.exists())
        self.assertIn("估价结果说明", artifacts.generated_fields)

    def test_registry_contains_expected_providers(self) -> None:
        providers = set(GLOBAL_LLM_REGISTRY.providers())
        self.assertTrue({"mock", "local", "qwen", "doubao", "kimi"}.issubset(providers))


if __name__ == "__main__":
    unittest.main(verbosity=2)
