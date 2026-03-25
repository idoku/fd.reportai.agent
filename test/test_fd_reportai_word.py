from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.messages import AIMessage


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word.config import (  # noqa: E402
    ComputedFieldConfig,
    ElementValue,
    ReportSectionConfig,
    SectionElementConfig,
    WordPipelineConfig,
)
from fd_reportai_word.exporters import PandocDocxExporter  # noqa: E402
from fd_reportai_word.pipeline import WordPipeline  # noqa: E402


class CountingModel:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = 0

    def invoke(self, input, config=None, **kwargs):
        self.calls += 1
        return AIMessage(content=self.content, response_metadata={"model_name": "counting-model"})


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

    def test_computed_field_is_resolved_once_and_reused(self) -> None:
        llm = CountingModel("Derived Project Name")

        cover_fragment = ReportSectionConfig(
            key="cover",
            title="Cover",
            block_mode="template_fill",
            template="Project: {project_name}",
            elements=[SectionElementConfig(key="project_name")],
        )
        summary_fragment = ReportSectionConfig(
            key="summary",
            title="Summary",
            block_mode="template_fill",
            template="Summary project: {valuation_project_name}",
            elements=[SectionElementConfig(key="valuation_project_name", source_key="project_name")],
        )

        framework = WordPipelineConfig(
            title="Computed Field Report",
            computed_fields=[
                ComputedFieldConfig(
                    key="project_name",
                    mode="llm_text",
                    prompt="Generate a project name from:\n{input}",
                    input_blocks=[],
                )
            ],
            sections=[cover_fragment, summary_fragment],
        )

        context = WordPipeline(llm=llm).run(framework=framework, elements={})

        self.assertEqual(context.composed_document["sections"][0]["content"], "Project: Derived Project Name")
        self.assertEqual(
            context.composed_document["sections"][1]["content"],
            "Summary project: Derived Project Name",
        )
        self.assertEqual(llm.calls, 1)
        self.assertEqual(context.blocked_items, [])
        self.assertEqual(context.validation_errors, [])

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
