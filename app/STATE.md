# STATE.md

> 记录当前正在执行到哪里，以及下一步接什么。
> 只保留当前上下文，不记录阶段历史。

## 当前阶段
Phase 3 - 要素系统（已完成）

## 当前焦点
校验 Phase 3 完整闭环，准备进入 Phase 4

## 当前断点
- 暂无（Phase 3 全部完成）

## 最近完成
- Phase 1 页面骨架完成（Streamlit 四区布局）
- Phase 2 模版结构读取完成（sidebar 接入真实 RULESET_LAND，差异化 fallback）
- Bug Fix: 右侧保存后中间预览即时更新
- Phase 3 要素系统完成：
  - 实现 element_resolver.py：节点 → 字段映射（合并 section.elements + content_items.elements，去重）
  - init_session 实现真实字段数据（不再依赖 MOCK_FIELDS）
  - element_panel: 字段剧评 * / (可选)，多行内容自动用 text_area
  - markdown 初始内容动态构建（不再依赖 MOCK_MARKDOWN）

## 下一步
Phase 4 - 文档预览
1. 实现 document_service.py
2. 支持节点预览 / 全文预览切换
3. 预览内容与 session 字段保持一致


## 当前焦点
将左侧节点树切换到 `ReportSession.template_tree`，完成真实模版结构展示闭环，并保留 mock fallback。

## 当前断点
- `app/ui/sidebar_tree.py` 仍直接使用 `MOCK_TEMPLATE_TREE`
- 左侧节点树尚未递归渲染 `children`
- 尚未验证 `fd_reportai_word` 加载失败时的 fallback 展示
- `app.py` 阶段文案仍停留在 Phase 1 / mock 数据

## 最近完成
- `core/config_loader.py` 已实现真实模版读取
- `load_template_nodes()` 已提供异常回退到 mock 的能力
- `init_session()` 已接入真实模版树加载
- 页面骨架、节点切换、字段编辑、预览、对话 stub 已完成

## 下一步
1. 改造 `ui/sidebar_tree.py` 使用 `session.template_tree`
2. 支持真实模版的层级渲染与节点选择
3. 验证 fallback 路径与页面稳定性
4. 更新 `PHASE.md` 记录 Phase 2 收尾结果
