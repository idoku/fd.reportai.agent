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
    ContentItemConfig,
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

    def test_computed_field_supports_fixed_and_extract_modes(self) -> None:
        cover_fragment = ReportSectionConfig(
            key="cover",
            title="Cover",
            block_mode="template_fill",
            template="Title: {report_title}\nClient: {client_name}\nDate: {submit_date}",
            elements=[
                SectionElementConfig(key="report_title"),
                SectionElementConfig(key="client_name"),
                SectionElementConfig(key="submit_date"),
            ],
        )

        framework = WordPipelineConfig(
            title="Extract Report",
            computed_fields=[
                ComputedFieldConfig(
                    key="report_title",
                    mode="fixed",
                    options={"value": "Land Report"},
                ),
                ComputedFieldConfig(
                    key="client_name",
                    mode="extract",
                    options={"path": "client.name"},
                ),
                ComputedFieldConfig(
                    key="submit_date",
                    mode="extract",
                    options={"path": "project.date", "transform": "cn_date"},
                ),
            ],
            sections=[cover_fragment],
        )

        context = WordPipeline().run(
            framework=framework,
            elements={
                "client": {"name": "Company A"},
                "project": {"date": "2025年12月10日"},
            },
        )

        self.assertEqual(
            context.composed_document["sections"][0]["content"],
            "Title: Land Report\nClient: Company A\nDate: 二〇二五年十二月十日",
        )
        self.assertEqual(context.blocked_items, [])
        self.assertEqual(context.validation_errors, [])

    def test_section_element_alias_reads_alternate_input_key(self) -> None:
        cover_fragment = ReportSectionConfig(
            key="cover",
            title="Cover",
            block_mode="template_fill",
            template="Client: {委托方}",
            elements=[
                SectionElementConfig(key="委托方", aliases=["委托方名称"]),
            ],
        )

        framework = WordPipelineConfig(
            title="Alias Report",
            sections=[cover_fragment],
        )

        context = WordPipeline().run(
            framework=framework,
            elements={"委托方名称": "长沙银行股份有限公司"},
        )

        self.assertEqual(context.composed_document["sections"][0]["content"], "Client: 长沙银行股份有限公司")
        self.assertEqual(context.blocked_items, [])
        self.assertEqual(context.validation_errors, [])

    def test_section_element_alias_reads_nested_input_and_applies_transform(self) -> None:
        cover_fragment = ReportSectionConfig(
            key="cover",
            title="Cover",
            block_mode="template_fill",
            template="Client: {委托方}\nDate: {提交日期}",
            elements=[
                SectionElementConfig(key="委托方", aliases=["委托方名称"]),
                SectionElementConfig(key="提交日期", aliases=["报告完成日期"], options={"transform": "cn_date"}),
            ],
        )

        framework = WordPipelineConfig(
            title="Alias Transform Report",
            sections=[cover_fragment],
        )

        context = WordPipeline().run(
            framework=framework,
            elements={
                "委托估价方": {"委托方名称": "长沙银行股份有限公司"},
                "项目信息": {"报告完成日期": "2025年12月10日"},
            },
        )

        self.assertEqual(
            context.composed_document["sections"][0]["content"],
            "Client: 长沙银行股份有限公司\nDate: 二〇二五年十二月十日",
        )
        self.assertEqual(context.blocked_items, [])
        self.assertEqual(context.validation_errors, [])

    def test_section_content_items_support_template_rendering(self) -> None:
        summary_fragment = ReportSectionConfig(
            key="summary",
            title="Summary",
            block_mode="template_fill",
            template="Client Info\n{委托估价方}",
            content_items=[
                ContentItemConfig(
                    key="委托估价方",
                    template="委托估价方：{委托方}\n联系人：{联系人}",
                    elements=[
                        SectionElementConfig(key="委托方", aliases=["委托方名称"]),
                        SectionElementConfig(key="联系人"),
                    ],
                )
            ],
        )

        framework = WordPipelineConfig(
            title="Content Item Report",
            sections=[summary_fragment],
        )

        context = WordPipeline().run(
            framework=framework,
            elements={
                "委托估价方": {
                    "委托方名称": "长沙银行股份有限公司",
                    "联系人": "王经理",
                }
            },
        )

        self.assertEqual(
            context.composed_document["sections"][0]["content"],
            "Client Info\n委托估价方：长沙银行股份有限公司\n联系人：王经理",
        )
        self.assertEqual(context.blocked_items, [])
        self.assertEqual(context.validation_errors, [])

    def test_section_content_item_supports_prompt_and_template(self) -> None:
        llm = CountingModel('{"结论":"通过提示词生成的内容"}')

        summary_fragment = ReportSectionConfig(
            key="summary",
            title="Summary",
            block_mode="template_fill",
            template="Result\n{说明}",
            content_items=[
                ContentItemConfig(
                    key="说明",
                    template="{结论}",
                    prompt="请根据输入生成 JSON：{{\"结论\":\"...\"}}\n输入：{input}",
                    elements=[SectionElementConfig(key="source")],
                )
            ],
        )

        framework = WordPipelineConfig(
            title="Prompt Content Item Report",
            sections=[summary_fragment],
        )

        context = WordPipeline(llm=llm).run(
            framework=framework,
            elements={"source": "demo"},
        )

        self.assertEqual(context.composed_document["sections"][0]["content"], "Result\n通过提示词生成的内容")
        self.assertEqual(llm.calls, 1)
        self.assertEqual(context.blocked_items, [])
        self.assertEqual(context.validation_errors, [])

    def test_llm_json_computed_field_exposes_child_fields_to_content_item(self) -> None:
        llm = CountingModel('{"term":"30 years","usage":"residential"}')

        summary_fragment = ReportSectionConfig(
            key="summary",
            title="Summary",
            block_mode="template_fill",
            template="{value_definition}",
            content_items=[
                ContentItemConfig(
                    key="value_definition",
                    template="Term: {term}\nUsage: {usage}",
                    elements=[
                        SectionElementConfig(key="term"),
                        SectionElementConfig(key="usage"),
                    ],
                )
            ],
        )

        framework = WordPipelineConfig(
            title="JSON Computed Field Report",
            computed_fields=[
                ComputedFieldConfig(
                    key="value_definition_items",
                    mode="llm_json",
                    prompt="Return JSON only.\n{input}",
                    input_blocks=[],
                )
            ],
            sections=[summary_fragment],
        )

        context = WordPipeline(llm=llm).run(framework=framework, elements={})

        self.assertEqual(context.composed_document["sections"][0]["content"], "Term: 30 years\nUsage: residential")
        self.assertEqual(llm.calls, 1)
        self.assertEqual(context.blocked_items, [])
        self.assertEqual(context.validation_errors, [])

    def test_llm_text_computed_field_renders_signatures_content(self) -> None:
        llm = CountingModel("姓   名      土地估价师证书号      签     字\n\n唐跃坤           94180084\n\n王玉           2004430018")

        summary_fragment = ReportSectionConfig(
            key="summary",
            title="Summary",
            block_mode="template_fill",
            template="{signatures}",
            content_items=[
                ContentItemConfig(
                    key="signatures",
                    template="{signatures}",
                    elements=[SectionElementConfig(key="signatures")],
                )
            ],
        )

        framework = WordPipelineConfig(
            title="Signature Report",
            computed_fields=[
                ComputedFieldConfig(
                    key="signatures",
                    mode="llm_text",
                    prompt="请生成签字内容：\n{input}",
                    input_blocks=[SectionElementConfig(key="估价师")],
                )
            ],
            sections=[summary_fragment],
        )

        context = WordPipeline(llm=llm).run(
            framework=framework,
            elements={
                "估价师": [
                    {"姓名": "唐跃坤", "土地估价师证书号": "94180084"},
                    {"姓名": "王玉", "土地估价师证书号": "2004430018"},
                ]
            },
        )

        self.assertEqual(
            context.composed_document["sections"][0]["content"],
            "姓   名      土地估价师证书号      签     字\n\n唐跃坤           94180084\n\n王玉           2004430018",
        )
        self.assertEqual(llm.calls, 1)
        self.assertEqual(context.blocked_items, [])
        self.assertEqual(context.validation_errors, [])

    def test_section_element_markdown_image_transform_renders_image_reference(self) -> None:
        summary_fragment = ReportSectionConfig(
            key="summary",
            title="Summary",
            block_mode="template_fill",
            template="{agency}",
            content_items=[
                ContentItemConfig(
                    key="agency",
                    template="签字：\n{signature}",
                    elements=[
                        SectionElementConfig(
                            key="signature",
                            aliases=["签字图片"],
                            options={"transform": "markdown_image"},
                        )
                    ],
                )
            ],
        )

        framework = WordPipelineConfig(
            title="Agency Report",
            sections=[summary_fragment],
        )

        context = WordPipeline().run(
            framework=framework,
            elements={"签字图片": "https://example.com/signature.png"},
        )

        self.assertEqual(
            context.composed_document["sections"][0]["content"],
            "签字：\n![法定代表人签字](<https://example.com/signature.png>)",
        )
        self.assertEqual(context.blocked_items, [])
        self.assertEqual(context.validation_errors, [])

    def test_section_element_markdown_image_transform_resolves_relative_path(self) -> None:
        summary_fragment = ReportSectionConfig(
            key="summary",
            title="Summary",
            block_mode="template_fill",
            template="{agency}",
            content_items=[
                ContentItemConfig(
                    key="agency",
                    template="{signature}",
                    elements=[
                        SectionElementConfig(
                            key="signature",
                            aliases=["签字图片"],
                            options={"transform": "markdown_image"},
                        )
                    ],
                )
            ],
        )

        framework = WordPipelineConfig(
            title="Agency Report",
            sections=[summary_fragment],
        )

        context = WordPipeline().run(
            framework=framework,
            elements={"签字图片": "法人签名.png"},
            metadata={"input_base_dir": str(ROOT / "inputs")},
        )

        expected_path = (ROOT / "inputs" / "法人签名.png").resolve().as_posix()
        self.assertEqual(
            context.composed_document["sections"][0]["content"],
            f"![法定代表人签字](<{expected_path}>)",
        )
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
