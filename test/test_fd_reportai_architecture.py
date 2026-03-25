from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word import DefaultAssembler, DefaultBlocker, DefaultComposer, DefaultPlanner, DefaultRenderer  # noqa: E402
from fd_reportai_word.domain import BlockDefinition, DataContext, DefinitionInput, ElementValue, ReportTemplate, SectionDefinition  # noqa: E402


class TestFdReportAiArchitecture(unittest.TestCase):
    def test_blocker_marks_missing_required_inputs(self) -> None:
        template = ReportTemplate(
            key="valuation_report_v1",
            sections=[
                SectionDefinition(
                    key="summary",
                    title="Summary",
                    blocks=[
                        BlockDefinition(
                            key="summary_block",
                            title="Summary",
                            template="Project: {project_name}",
                            inputs=[DefinitionInput(key="project_name")],
                        )
                    ],
                )
            ],
        )
        plan = DefaultPlanner().plan(template)
        sections, blocked_items = DefaultBlocker().build(plan, DataContext(values={}))

        self.assertEqual(sections[0].tasks[0].missing_required_inputs, ["project_name"])
        self.assertEqual(blocked_items[0]["block_key"], "summary_block")

    def test_assembler_keeps_structured_block_results(self) -> None:
        template = ReportTemplate(
            key="valuation_report_v1",
            version="v1",
            title="Valuation Report",
            sections=[
                SectionDefinition(
                    key="summary",
                    title="Summary",
                    blocks=[
                        BlockDefinition(
                            key="summary_block",
                            title="Summary",
                            template="Project: {project_name}",
                            inputs=[DefinitionInput(key="project_name")],
                        )
                    ],
                )
            ],
        )
        plan = DefaultPlanner().plan(template)
        data_context = DataContext(
            values={"project_name": ElementValue(value="FD Tower")},
            metadata={"template_version": "v1", "rule_version": "rules-1"},
            snapshot_id="snapshot-1",
        )
        sections, blocked_items = DefaultBlocker().build(plan, data_context)
        result = DefaultComposer().compose(sections[0].tasks[0], data_context)
        document = DefaultAssembler().assemble(
            title=template.title,
            template_key=plan.template_key,
            template_version=plan.template_version,
            sections=sections,
            block_results={(result.section_key, result.block_key): result},
            blocked_items=blocked_items,
            metadata={"request_id": "req-1"},
        )

        self.assertEqual(document.sections[0].blocks[0].content["type"], "rich_text")
        self.assertEqual(document.sections[0].blocks[0].trace.data_snapshot_id, "snapshot-1")
        self.assertEqual(document.metadata["request_id"], "req-1")

    def test_renderer_outputs_trace_and_validation(self) -> None:
        template = ReportTemplate(
            key="valuation_report_v1",
            version="v1",
            title="Valuation Report",
            sections=[
                SectionDefinition(
                    key="summary",
                    title="Summary",
                    blocks=[
                        BlockDefinition(
                            key="summary_block",
                            title="Summary",
                            template="Project: {project_name}",
                            inputs=[DefinitionInput(key="project_name")],
                        )
                    ],
                )
            ],
        )
        plan = DefaultPlanner().plan(template)
        data_context = DataContext(
            values={"project_name": ElementValue(value="FD Tower")},
            metadata={"template_version": "v1", "rule_version": "rules-1"},
            snapshot_id="snapshot-1",
        )
        sections, blocked_items = DefaultBlocker().build(plan, data_context)
        result = DefaultComposer().compose(sections[0].tasks[0], data_context)
        document = DefaultAssembler().assemble(
            title=template.title,
            template_key=plan.template_key,
            template_version=plan.template_version,
            sections=sections,
            block_results={(result.section_key, result.block_key): result},
            blocked_items=blocked_items,
        )
        rendered = DefaultRenderer().render(document)

        self.assertEqual(rendered["sections"][0]["blocks"][0]["trace"]["data_snapshot_id"], "snapshot-1")
        self.assertTrue(rendered["sections"][0]["blocks"][0]["validation"]["is_valid"])


if __name__ == "__main__":
    unittest.main()
