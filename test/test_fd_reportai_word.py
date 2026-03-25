from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"
INPUTS_DIR = ROOT / "inputs"
OUTPUTS_DIR = INPUTS_DIR / "_outputs"
LAND_SUMMARY_INPUT_PATH = INPUTS_DIR / "land_summary_input.json"
LAND_SUMMARY_OUTPUT_PATH = OUTPUTS_DIR / "land_summary.md"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word.config import ElementValue, ReportSectionConfig, SectionElementConfig, WordPipelineConfig  # noqa: E402
from fd_reportai_word.exporters import PandocDocxExporter  # noqa: E402
from fd_reportai_word.pipeline import WordPipeline  # noqa: E402
from fd_reportai_word.rules import get_default_ruleset  # noqa: E402


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class TestFdReportAiWord(unittest.TestCase):
    def test_pipeline_with_elements_fragment_and_framework(self) -> None:
        elements = {
            "company_name": "FD",
            "summary": ElementValue(value="Growth remains stable."),
            "risk_points": ElementValue(value=["Receivables", "Margin pressure"]),
        }

        summary_fragment = ReportSectionConfig(
            key="summary",
            title="Summary",
            block_mode="template_fill",
            template="Company: {company_name}\nSummary: {summary}",
            elements=[
                SectionElementConfig(key="company_name"),
                SectionElementConfig(key="summary"),
            ],
        )

        risk_fragment = ReportSectionConfig(
            key="risk",
            title="Risk",
            block_mode="prompt_generation",
            template="Generate a concise risk section",
            prompt="Based on {company_name}, summarize risks from {risk_points}.",
            few_shots=[
                {
                    "input": "Company A, [Supply chain, FX]",
                    "output": "Key risks include supply chain disruption and FX volatility.",
                }
            ],
            elements=[
                SectionElementConfig(key="company_name"),
                SectionElementConfig(key="risk_points"),
            ],
        )

        framework = WordPipelineConfig(
            title="Simple Report",
            sections=[summary_fragment, risk_fragment],
        )

        context = WordPipeline().run(framework=framework, elements=elements)

        self.assertEqual(context.composed_document["title"], "Simple Report")
        self.assertEqual(len(context.composed_document["sections"]), 2)
        self.assertEqual(
            context.composed_document["sections"][0]["content"],
            "Company: FD\nSummary: Growth remains stable.",
        )
        self.assertEqual(
            context.composed_document["sections"][1]["content"]["mode"],
            "prompt_generation",
        )
        self.assertIn("# Simple Report", context.rendered_output["markdown"])
        self.assertIn("## Summary", context.rendered_output["markdown"])
        self.assertIn("Company: FD\nSummary: Growth remains stable.", context.rendered_output["markdown"])
        self.assertEqual(context.composed_document["blocked_items"], [])
        self.assertEqual(context.validation_errors, [])

    def test_pipeline_loads_markdown_and_prompt_from_default_ruleset(self) -> None:
        framework = get_default_ruleset("valuation_report")
        context = WordPipeline().run(
            framework=framework,
            elements={
                "project_name": "Alpha Project",
                "valuation_conclusion": "Market value remains stable.",
                "income": 100,
                "ebitda": 20,
            },
            metadata={
                "compute_registry": {
                    "build_metrics_table": lambda variables, task=None: [
                        ["income", variables["income"]],
                        ["ebitda", variables["ebitda"]],
                    ],
                    "build_site_photos": lambda variables, task=None: [],
                }
            },
        )

        self.assertEqual(context.framework.name, "valuation_report_v1")
        self.assertIn("Project: Alpha Project", context.composed_document["sections"][0]["content"])
        analysis_content = context.composed_document["sections"][2]["content"]
        self.assertEqual(analysis_content["mode"], "prompt_generation")
        self.assertIn("Alpha Project", analysis_content["prompt"])
        self.assertIn("Market value remains stable.", analysis_content["prompt"])

    def test_pipeline_reads_land_summary_inputs_from_default_ruleset(self) -> None:
        summary_input = load_json(LAND_SUMMARY_INPUT_PATH)
        framework = get_default_ruleset("land_conver")

        context = WordPipeline().run(framework=framework, elements=summary_input)
        sections = context.composed_document["sections"]
        rendered_markdown = context.rendered_output["markdown"]

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        LAND_SUMMARY_OUTPUT_PATH.write_text(rendered_markdown, encoding="utf-8")

        self.assertEqual(context.framework.name, "land_conver_v1")
        self.assertEqual([section["key"] for section in sections], ["conver", "summary"])
        self.assertTrue(sections[1]["content"])
        self.assertIn(sections[1]["title"], rendered_markdown)
        self.assertTrue(LAND_SUMMARY_OUTPUT_PATH.exists())
        self.assertEqual(LAND_SUMMARY_OUTPUT_PATH.read_text(encoding="utf-8"), rendered_markdown)

    @patch("fd_reportai_word.exporters.pandoc.subprocess.run")
    def test_pandoc_exporter_builds_docx_command(self, mock_run) -> None:
        exporter = PandocDocxExporter()
        output_path = ROOT / "test-output" / "sample.docx"

        result = exporter.export(
            "# Sample Report\n\nHello, **Markdown**.",
            output_path,
            reference_doc=ROOT / "test-output" / "reference.docx",
        )

        self.assertEqual(result, output_path)
        command = mock_run.call_args.args[0]
        self.assertEqual(command[0], "pandoc")
        self.assertIn("-f", command)
        self.assertIn("markdown", command)
        self.assertIn("-t", command)
        self.assertIn("docx", command)
        self.assertIn("--reference-doc", command)
        self.assertEqual(command[-1], str(ROOT / "test-output" / "reference.docx"))


if __name__ == "__main__":
    unittest.main()
