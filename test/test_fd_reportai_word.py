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

from fd_reportai_word import get_default_ruleset  # noqa: E402
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

    def test_land_ruleset_renders_result_table_from_structured_elements(self) -> None:
        framework = get_default_ruleset("ruleset_land")

        context = WordPipeline().run(
            framework=framework,
            elements={
                "项目信息": {
                    "估价机构": "湖南经典房地产评估咨询有限公司",
                    "报告编号": "湘经典（2025）（估）字第娄土003411A号",
                    "报告完成日期": "2025年12月16日",
                    "查勘完成日期": "2025年11月7日",
                    "估价目的": "抵押贷款",
                    "估价期日的土地使用权性质": "国有出让",
                },
                "项目名称": "冷水江市创新实业有限公司土地抵押估价项目",
                "委托估价方": {
                    "委托方名称": "长沙银行娄底分行",
                    "联系人": "王经理",
                    "联系方式": "13575205309",
                },
                "委托方与权利人关系": "委托方为贷款银行，权利人为抵押人。",
                "估价对象界定": "估价对象为位于冷水江市的两宗国有出让商服、住宅用地。",
                "估价目的描述": "本次评估为抵押贷款提供土地使用权价格参考依据。",
                "期日设定": "估价期日为2025年11月7日。",
                "用途设定": "设定用途为商服、住宅用地。",
                "权利类型设定": "设定权利类型为国有出让土地使用权。",
                "年限设定": "商服剩余年限38.37年，住宅剩余年限68.37年。",
                "利用条件设定": "设定利用条件为规划利用条件。",
                "开发程度设定": "宗地红线外“五通”及红线内场地未平整。",
                "他项权利设定": "估价期日已设立抵押权他项权利登记。",
                "价格内涵总结": "在规划利用条件下的国有出让土地使用权价格。",
                "估价结果描述": "估价对象总地价为28854544元。",
                "估价结果说明": "估价结果详见附表《土地估价结果一览表》（表1-1）。",
                "估价师签字": "唐跃坤  94180084\n王玉  2004430018",
                "估价师": [
                    {"姓名": "唐跃坤", "土地估价师证书号": "94180084"},
                    {"姓名": "王玉", "土地估价师证书号": "2004430018"},
                ],
                "估价机构": "湖南经典房地产评估咨询有限公司",
                "法人签名": "法人签名.png",
                "估价对象": [
                    {
                        "土地使用者": "冷水江市创新实业有限公司",
                        "宗地编号": "1",
                        "宗地名称": "冷水江市创新实业有限公司",
                        "不动产权证书证号": "湘（2024）冷水江市不动产权第0001351号",
                        "用途": {"证载": "商服、住宅用地", "实际": "/", "设定": "商服、住宅用地"},
                        "容积率": {"规划": "不小于1.0，不大于4.0", "实际": "/", "设定": "4.0"},
                        "开发程度": {
                            "实际": "宗地红线外“五通”及红线内场地未平整",
                            "设定": "宗地红线外“五通”及红线内场地未平整",
                        },
                        "剩余年限": "商服38.37年、住宅68.37年",
                        "面积_平方米": 4666,
                        "单价_元": 3092,
                        "总地价_元": 14427272,
                        "备注": "/",
                    },
                    {
                        "土地使用者": "冷水江市创新实业有限公司",
                        "宗地编号": "2",
                        "宗地名称": "冷水江市城东生态城资江大道东侧",
                        "不动产权证书证号": "湘（2024）冷水江市不动产权第0001350号",
                        "用途": {"证载": "商服、住宅用地", "实际": "/", "设定": "商服、住宅用地"},
                        "容积率": {"规划": "不小于1.0，不大于4.0", "实际": "/", "设定": "4.0"},
                        "开发程度": {
                            "实际": "宗地红线外“五通”及红线内场地未平整",
                            "设定": "宗地红线外“五通”及红线内场地未平整",
                        },
                        "剩余年限": "商服38.37年、住宅68.37年",
                        "面积_平方米": 4666,
                        "单价_元": 3092,
                        "总地价_元": 14427272,
                        "备注": "",
                    },
                    {"合计": {"面积_平方米": 9332, "总地价_元": 28854544}},
                ],
                "限定条件": [
                    "土地权利限制：估价对象1-2至估价期日，已设立抵押权他项权利登记。",
                    "基础设施条件：宗地内场地未平整，供水、排水、供电、通讯条件较好。",
                ],
                "其他说明事项": [
                    "本估价结果仅作为抵押贷款提供土地使用权价格参考依据。",
                    "本报告评估结果自提交日期起有效期壹年。",
                ],
            },
            metadata={"input_base_dir": str(ROOT / "inputs")},
        )

        markdown = context.rendered_output["markdown"]

        self.assertIn("表1-1  土地估价结果一览表", markdown)
        self.assertIn("估价机构：湖南经典房地产评估咨询有限公司", markdown)
        self.assertIn("估价目的：抵押贷款", markdown)
        self.assertIn("估价期日的土地使用权性质：国有出让", markdown)
        self.assertIn("| 估价期日的土地使用者 | 宗地编号 | 宗地名称 |", markdown)
        self.assertIn("冷水江市城东生态城资江大道东侧", markdown)
        self.assertIn("| 总计 | / | / | / |", markdown)
        self.assertIn("9332", markdown)
        self.assertIn("28854544", markdown)
        self.assertIn("1、土地权利限制", markdown)
        self.assertIn("1、本估价结果仅作为抵押贷款提供土地使用权价格参考依据。", markdown)
        self.assertNotIn("{结果一览表表格}", markdown)
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
