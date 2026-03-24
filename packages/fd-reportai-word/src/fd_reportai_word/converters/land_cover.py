from __future__ import annotations

from .base import BaseConverter
from ..config import ElementValue
from ..context import WordContext


class LandValuationCoverConverter(BaseConverter):
    def convert(self, context: WordContext) -> None:
        for detection in context.detections:
            if detection.get("key") != "land_valuation_cover":
                continue

            payload = detection.get("payload", {})
            context.elements.update(
                {
                    "report_title": ElementValue(value=payload.get("报告标题", "")),
                    "project_name": ElementValue(value=payload.get("项目名称", "")),
                    "entrusting_party": ElementValue(value=payload.get("委托方", "")),
                    "report_number": ElementValue(value=payload.get("报告编号", "")),
                    "submit_date": ElementValue(value=payload.get("提交日期", "")),
                }
            )
            context.converted_blocks.append(
                {
                    "key": "land_valuation_cover",
                    "type": "cover_page",
                    "content": payload,
                }
            )
