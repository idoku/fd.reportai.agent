# PHASE.md

> 记录已经完成的阶段性结果与历史产出。
> 只追加，不回写当前执行状态与未来计划。

## Phase 1 - 页面骨架（已完成）

### 执行时间
2026-04-03

### 阶段目标
搭建 Report Studio 基础页面骨架，形成可运行的最小闭环

---

### 主要变更
- 创建 app.py
- 实现四区布局（sidebar / element / preview / chat）
- 接入 mock 数据
- 完成节点切换与基础交互

---

### 阶段产出
- 可运行的 Streamlit 页面
- 四区布局结构（后续扩展基础）
- mock 数据驱动的完整流程（结构浏览 → 编辑 → 预览 → 对话）

---

### 当前结果
- 页面可正常运行
- mock 数据闭环完整
- 基础交互正常（节点切换 / 编辑 / 预览）

---

### 遗留问题
- 模版结构仍为 mock 数据
- 未接入 fd_reportai_word 配置
- 未实现字段映射与真实数据驱动

---

## Phase 2 - 模版结构读取（已完成）

### 执行时间
2026-04-03

### 阶段目标
将左侧模版树切换为真实配置数据源，打通 fd_reportai_word → ReportSession → sidebar_tree

---

### 主要变更
- config_loader.py：load_template_nodes() 从 RULESET_LAND 读取真实章节，fallback mock
- element_resolver.py：resolve_all_fields() 从 RULESET_LAND 提取字段
- sidebar_tree.py：改用 session.template_tree（而非硬编码 MOCK_TEMPLATE_TREE）

---

### 阶段产出
- 左侧展示真实模版结构（cover / summary / object_definition / result_usage / attachments）
- 节点切换正常

---

### 当前结果
- 左侧展示真实模版结构
- fd_reportai_word 不可用时自动回退 mock

---

### 遗留问题
- 模版树仅一层（content_items 未展示为子节点）→ Phase 5 修复

---

## Phase 3 - 要素系统（已完成）

### 执行时间
2026-04-03

### 阶段目标
建立节点与字段的映射关系，右侧编辑区提供真实字段

---

### 主要变更
- element_resolver.py：_extract_fields 提取 section 顶层元素 + content_item 元素
- session.py：update_field / rebuild_preview_from_fields
- element_panel.py：表单驱动字段编辑，保存后触发 rebuild_preview

---

### 阶段产出
- 右侧展示真实字段（从 RULESET_LAND 读取）
- 字段保存后 session 同步更新
- 中间预览即时更新（字段表格形式）

---

### 遗留问题
- 要素内容读取有时为空 → Phase 5 修复（content_item key 索引）

---

## Phase 4 - 文档预览（已完成）

### 执行时间
2026-04-03

### 阶段目标
支持节点级预览和全文预览切换

---

### 主要变更
- document_service.py：build_node_markdown / build_full_markdown
- session.py：preview_mode 字段
- document_preview.py：radio 切换节点/全文预览

---

### 阶段产出
- 节点预览 / 全文预览可切换
- 全文预览 DFS 遍历 template_tree，各节点以 --- 分隔

---

## Phase 5 - 文档生成（已完成）

### 执行时间
2026-04-03

### 阶段目标
接入 fd_reportai_word pipeline，生成模板 markdown 并写回预览

---

### 主要变更
- app/adapters/report_adapter.py（新建）：调用 WordPipeline，提取各章节 markdown
- document_service.py：新增 generate_markdown_from_pipeline()
- document_preview.py：新增「⚡ 生成预览」按钮
- config_loader.py：_section_to_node 支持两层（章节 + content_items 子节点）
- element_resolver.py：按 content_item key 建立字段索引
- sidebar_tree.py：改用 session.template_tree，支持两层渲染
- app.py：caption 更新为 Phase 5

---

### 阶段产出
- 可点击「⚡ 生成预览」生成模板 markdown（无 LLM 模式，占位符保留）
- 生成结果即时写回 session.markdown 并触发预览更新
- 左侧模版树展示两层结构（章节 + 内容项）
- 要素内容可正常读取

---

### 当前结果
- Phase 5 验收条件全部满足
- 无阻塞性报错

---

### 遗留问题
- 生成结果含占位符（{xxx}），接入真实 LLM 后会消失 → Phase 6
