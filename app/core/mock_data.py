"""
mock_data.py — Phase 1 静态 mock 数据，不依赖任何外部系统。
所有数据基于 land_input.json / LandInfo.py 的土地估价要素原型。
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# 模版节点树（扁平列表，key 唯一）                                               #
# --------------------------------------------------------------------------- #

MOCK_TEMPLATE_TREE: list[dict] = [
    {"key": "cover",              "title": "封面",                  "children": []},
    {"key": "summary",            "title": "摘要",                  "children": []},
    {"key": "object_definition",  "title": "估价对象界定",           "children": []},
    {"key": "result_usage",       "title": "土地估价结果及其使用",    "children": []},
    {"key": "attachments",        "title": "附件",                  "children": []},
]

# --------------------------------------------------------------------------- #
# 字段列表  node_key -> [{key, label, value}]                                  #
# --------------------------------------------------------------------------- #

MOCK_FIELDS: dict[str, list[dict]] = {
    "cover": [
        {"key": "report_no",   "label": "报告编号",   "value": "湘经典（2025）（估）字第常土003912A号"},
        {"key": "org_name",    "label": "估价机构",   "value": "湖南经典房地产评估咨询有限公司"},
        {"key": "finish_date", "label": "报告完成日期", "value": "2025年12月10日"},
        {"key": "purpose",     "label": "估价目的",   "value": "抵押贷款"},
        {"key": "mortgagor",   "label": "抵押人",     "value": "冷水江市创新实业有限公司"},
    ],
    "summary": [
        {"key": "total_value", "label": "评估总价（万元）", "value": "2580.00"},
        {"key": "unit_price",  "label": "评估单价（元/㎡）", "value": "806.25"},
        {"key": "value_date",  "label": "估价时点",   "value": "2025年12月1日"},
        {"key": "method",      "label": "估价方法",   "value": "市场比较法、成本法"},
    ],
    "object_definition": [
        {"key": "land_user",   "label": "土地使用者",  "value": "冷水江市创新实业有限公司"},
        {"key": "parcel_no",   "label": "宗地编号",   "value": "1"},
        {"key": "cert_no",     "label": "不动产权证书证号", "value": "湘（2024）冷水江市不动产权第0001351号"},
        {"key": "use_type",    "label": "土地用途",   "value": "商服、住宅用地"},
        {"key": "area",        "label": "宗地面积（㎡）", "value": "3200.00"},
        {"key": "term",        "label": "使用年限（年）", "value": "40/70"},
        {"key": "location",    "label": "宗地坐落",   "value": "冷水江市中心区域"},
    ],
    "result_usage": [
        {"key": "client",      "label": "委托方",     "value": "长沙银行股份有限公司"},
        {"key": "contact",     "label": "联系人",     "value": "王经理"},
        {"key": "phone",       "label": "联系方式",   "value": "13575205309"},
        {"key": "usage_note",  "label": "用途说明",   "value": "用于抵押贷款参考依据，不得用于其他目的"},
    ],
    "attachments": [
        {"key": "location_map",  "label": "位置图",     "value": "location_map.png"},
        {"key": "cadastral_map", "label": "地籍图",     "value": "cadastral_map.png"},
        {"key": "cert_copy",     "label": "证书复印件", "value": "cert_copy.pdf"},
    ],
}

# --------------------------------------------------------------------------- #
# Markdown 预览内容  node_key -> markdown str                                  #
# --------------------------------------------------------------------------- #

MOCK_MARKDOWN: dict[str, str] = {
    "cover": """\
# 土地估价报告

**估价机构**：湖南经典房地产评估咨询有限公司

**报告编号**：湘经典（2025）（估）字第常土003912A号

**报告完成日期**：2025年12月10日

**估价目的**：抵押贷款

**抵押人**：冷水江市创新实业有限公司
""",
    "summary": """\
## 摘要

| 项目 | 内容 |
|------|------|
| 评估总价 | **2,580.00 万元** |
| 评估单价 | **806.25 元/㎡** |
| 估价时点 | 2025年12月1日 |
| 估价方法 | 市场比较法、成本法 |

> 以上评估结果仅供参考，实际价格以市场交易为准。
""",
    "object_definition": """\
## 一、估价对象界定

**土地使用者**：冷水江市创新实业有限公司

**宗地编号**：1

**不动产权证书证号**：湘（2024）冷水江市不动产权第0001351号

**土地用途**：商服、住宅用地

**宗地面积**：3,200.00 ㎡

**使用年限**：商服40年 / 住宅70年

**宗地坐落**：冷水江市中心区域
""",
    "result_usage": """\
## 三、估价结果与使用说明

**委托方**：长沙银行股份有限公司

**联系人**：王经理　**联系方式**：13575205309

### 使用限制

本报告仅用于**抵押贷款**参考依据，不得用于其他目的。
报告有效期自报告完成之日起一年内有效。
""",
    "attachments": """\
## 四、附件目录

1. 宗地位置图
2. 地籍图
3. 不动产权证书复印件
""",
}
