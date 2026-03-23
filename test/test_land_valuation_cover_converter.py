from __future__ import annotations

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word.config import ElementValue, ReportSectionConfig, SectionElementConfig, WordPipelineConfig  # noqa: E402
from fd_reportai_word.context import WordContext  # noqa: E402
from fd_reportai_word.converters import BaseConverter  # noqa: E402
from fd_reportai_word.pipeline import WordPipeline  # noqa: E402


def debug_print(label: str, value: object) -> None:
    print(f"{label}: {value}")


class LandValuationCoverConverter(BaseConverter):
    def convert(self, context: WordContext) -> None:
        print("[converter] start convert")
        print(f"[converter] detections count: {len(context.detections)}")

        for index, detection in enumerate(context.detections):
            debug_print(f"[converter] detection[{index}]", detection)
            if detection.get("key") != "land_valuation_cover":
                print(f"[converter] skip detection[{index}] because key={detection.get('key')}")
                continue

            payload = detection.get("payload", {})
            debug_print("[converter] matched payload", payload)

            context.elements.update(
                {
                    "report_title": ElementValue(value=payload.get("report_title", "")),
                    "project_name": ElementValue(value=payload.get("project_name", "")),
                    "entrusting_party": ElementValue(value=payload.get("entrusting_party", "")),
                    "report_number": ElementValue(value=payload.get("report_number", "")),
                    "submit_date": ElementValue(value=payload.get("submit_date", "")),
                }
            )
            debug_print("[converter] elements after update", context.elements)

            context.converted_blocks.append(
                {
                    "key": "land_valuation_cover",
                    "type": "cover_page",
                    "content": payload,
                }
            )
            debug_print("[converter] converted_blocks after append", context.converted_blocks)

        print("[converter] convert finished")


class TestLandValuationCoverConverter(unittest.TestCase):
    def test_converter_builds_cover_page_elements_for_template(self) -> None:
        print("\n[test] start test_converter_builds_cover_page_elements_for_template")

        cover_template = ReportSectionConfig(
            key="cover_page",
            title="Land Valuation Report Cover",
            block_mode="template_fill",
            template=(
                "{report_title}\n\n"
                "Project Name: {project_name}\n"
                "Entrusted Appraiser: {entrusting_party}\n"
                "Report Number: {report_number}\n"
                "Submission Date: {submit_date}"
            ),
            elements=[
                SectionElementConfig(key="report_title"),
                SectionElementConfig(key="project_name"),
                SectionElementConfig(key="entrusting_party"),
                SectionElementConfig(key="report_number"),
                SectionElementConfig(key="submit_date"),
            ],
        )
        debug_print("[test] cover_template", cover_template)

        framework = WordPipelineConfig(
            name="land_valuation_report",
            version="v1",
            title="Land Valuation Report",
            sections=[cover_template],
        )
        debug_print("[test] framework", framework)

        context = WordContext(
            framework=framework,
            metadata={"data_snapshot_id": "cover-snapshot-1"},
            detections=[
                {
                    "key": "land_valuation_cover",
                    "payload": {
                        "report_title": "土地估价报告",
                        "project_name": (
                            "长沙银行股份有限公司委托评估的冷水江市创新实业有限公司办理抵押贷款涉及的"
                            "冷水江市创新实业有限公司位于冷水江市城东生态城资江大道东侧的"
                            "二宗商服、住宅用地国有出让土地使用权抵押价值评估"
                        ),
                        "entrusting_party": "湖南经典房地产评估咨询有限公司",
                        "report_number": "湘经估（2025）（估）字第宗土003411A号",
                        "submit_date": "二〇二五年十二月十六日",
                    },
                }
            ],
        )
        debug_print("[test] context metadata", context.metadata)
        debug_print("[test] context detections", context.detections)

        pipeline = WordPipeline(converters=[LandValuationCoverConverter()])
        debug_print("[test] pipeline converters", pipeline.converters)

        result = pipeline.run(context=context)
        debug_print("[test] result elements", result.elements)
        debug_print("[test] result converted_blocks", result.converted_blocks)
        debug_print("[test] result blocked_items", result.blocked_items)
        debug_print("[test] result validation_errors", result.validation_errors)
        debug_print("[test] composed_document", result.composed_document)

        rendered_cover = result.composed_document["sections"][0]["content"]
        debug_print("[test] rendered_cover", rendered_cover)

        self.assertEqual(result.elements["report_title"].value, "土地估价报告")
        self.assertIn("Project Name:", rendered_cover)
        self.assertIn("土地估价报告", rendered_cover)
        self.assertIn("湘经估（2025）（估）字第宗土003411A号", rendered_cover)
        self.assertEqual(result.blocked_items, [])
        self.assertEqual(result.validation_errors, [])
        self.assertEqual(result.converted_blocks[0]["type"], "cover_page")
        print("[test] assertions passed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
