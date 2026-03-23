# fd-reportai-word

`fd-reportai-word` 现在按 `domain / application` 的结构维护核心报告生成链路，并保留 `WordPipeline` 作为兼容入口。

当前最小链路：

`ReportTemplate -> GenerationPlan -> BlockTask -> BlockResult -> ReportDocument -> RendererOutput`

已支持：

- `block_type`: `rich_text` / `table` / `image_group`
- `generator_mode`: `template` / `computed` / `ai`（预留接口）
- block 级 trace、输入快照、基础校验

示例入口使用 `valuation_report_v1`。
