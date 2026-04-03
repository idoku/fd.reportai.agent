# STATE.md

> 记录当前正在执行到哪里，以及下一步接什么。
> 只保留当前上下文，不记录阶段历史。

## 当前阶段
Phase 5 - 文档生成（已完成）

## 当前焦点
校验 Phase 5 完整闭环，准备进入 Phase 6

## 当前断点
- 暂无（Phase 5 全部完成）

## 最近完成
- Phase 1 页面骨架完成（Streamlit 四区布局）
- Phase 2 模版结构读取完成（sidebar 接入真实 RULESET_LAND，差异化 fallback）
- Bug Fix: 右侧保存后中间预览即时更新
- Phase 3 要素系统完成（element_resolver.py，真实字段映射，动态 markdown）
- Phase 4 文档预览完成（节点/全文预览切换，document_service.py）
- Bug Fix: sidebar_tree.py 改用 session.template_tree（不再固定读 MOCK_TEMPLATE_TREE）
- Bug Fix: element_resolver 按 content_item key 建立索引，要素内容可正常读取
- Feature: config_loader 两层结构（章节 + content_items）
- Phase 5 文档生成完成：
  - 实现 app/adapters/report_adapter.py：调用 fd_reportai_word pipeline（无 LLM）生成模板 markdown
  - 新增 generate_markdown_from_pipeline()：写回 session.markdown
  - document_preview.py 新增「⚡ 生成预览」按钮

## 下一步
Phase 6 - 对话能力
1. 接入 graph 层（LangGraph）
2. 让对话可以驱动字段修改
3. 支持通过对话触发内容生成
