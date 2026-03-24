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

from fd_reportai_word.config import (  # noqa: E402
    DEFAULT_RULES_DIR,
    ElementValue,
    ReportSectionConfig,
    SectionElementConfig,
    WordPipelineConfig,
)
from fd_reportai_word.exporters import PandocDocxExporter  # noqa: E402
from fd_reportai_word.pipeline import WordPipeline  # noqa: E402


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

        pipeline = WordPipeline()
        context = pipeline.run(framework=framework, elements=elements)

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

    def test_pipeline_loads_markdown_and_prompt_from_rules_directory(self) -> None:
        framework = WordPipelineConfig(
            name="valuation_report_v1",
            title="Valuation Report",
            version="v1",
            rules_dir=DEFAULT_RULES_DIR,
            sections=[
                ReportSectionConfig(
                    key="summary",
                    title="Summary",
                    block_mode="template_fill",
                    template_file="valuation/summary.md",
                    elements=[
                        SectionElementConfig(key="project_name"),
                        SectionElementConfig(key="valuation_conclusion"),
                    ],
                ),
                ReportSectionConfig(
                    key="analysis",
                    title="Analysis",
                    block_mode="prompt_generation",
                    prompt_file="valuation/analysis.prompt.md",
                    elements=[
                        SectionElementConfig(key="project_name"),
                        SectionElementConfig(key="valuation_conclusion"),
                    ],
                ),
            ],
        )
        pipeline = WordPipeline()
        context = pipeline.run(
            framework=framework,
            elements={
                "project_name": "Alpha Project",
                "valuation_conclusion": "Market value remains stable.",
            },
        )

        self.assertIn("Project: Alpha Project", context.composed_document["sections"][0]["content"])
        analysis_content = context.composed_document["sections"][1]["content"]
        self.assertEqual(analysis_content["mode"], "prompt_generation")
        self.assertIn("Alpha Project", analysis_content["prompt"])
        self.assertIn("Market value remains stable.", analysis_content["prompt"])

    def test_pipeline_reads_land_summary_inputs_from_path(self) -> None:
        summary_input = load_json(LAND_SUMMARY_INPUT_PATH)
        framework = WordPipelineConfig(
            name="land_summary_v1",
            title="土地估价报告",
            version="v1",
            rules_dir=DEFAULT_RULES_DIR,
            sections=[
                ReportSectionConfig(
                    key="summary",
                    title="摘要",
                    block_mode="template_fill",
                    template_file="land/land_summary.md",
                    elements=[
                        SectionElementConfig(key="估价项目名称"),
                        SectionElementConfig(key="委托估价方"),
                        SectionElementConfig(key="联系人"),
                        SectionElementConfig(key="联系方式"),
                        SectionElementConfig(key="委托方与权利人关系"),
                        SectionElementConfig(key="估价目的"),
                        SectionElementConfig(key="估价期日"),
                        SectionElementConfig(key="估价日期"),
                        SectionElementConfig(key="地价定义"),
                        SectionElementConfig(key="估价结果说明"),
                        SectionElementConfig(key="估价结果明细"),
                        SectionElementConfig(key="估价结果合计"),
                        SectionElementConfig(key="土地估价师签字表"),
                        SectionElementConfig(key="估价机构法定代表人签字", required=False, default_value=""),
                        SectionElementConfig(key="估价机构"),
                        SectionElementConfig(key="摘要出具日期"),
                        SectionElementConfig(key="结果一览表机构信息"),
                        SectionElementConfig(key="结果一览表目的与权性质"),
                        SectionElementConfig(key="结果一览表表格"),
                        SectionElementConfig(key="结果一览表备注"),
                        SectionElementConfig(key="限定条件"),
                        SectionElementConfig(key="其他说明事项"),
                    ],
                )
            ],
        )

        context = WordPipeline().run(framework=framework, elements=summary_input)
        rendered = context.composed_document["sections"][0]["content"]
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        LAND_SUMMARY_OUTPUT_PATH.write_text(context.rendered_output["markdown"], encoding="utf-8")

        self.assertIn("第一部分  摘  要", rendered)
        self.assertIn("长沙银行股份有限公司委托评估的常德市德源投资集团有限公司拟抵押贷款涉及的位于常德市经济技术开发区尚德路以东、民建路以北及常德经济技术开发区谢家湖的4宗国有出让建设用地", rendered)
        self.assertIn("七、估价结果", rendered)
        self.assertIn("估价对象1：", rendered)
        self.assertIn("表1-1  土地估价结果一览表", rendered)
        self.assertIn("| 估价对象 | 不动产权利人 | 坐落 |", rendered)
        self.assertIn("二、其他需要说明的事项：", rendered)
        self.assertTrue(LAND_SUMMARY_OUTPUT_PATH.exists())

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
