# STATE.md

> 记录当前正在执行到哪里，以及下一步接什么。
> 只保留当前上下文，不记录阶段历史。

## 当前阶段
Phase 4 - 文档预览（已完成）

## 当前焦点
校验 Phase 4 完整闭环，准备进入 Phase 5

## 当前断点
- 暂无（Phase 4 全部完成）

## 最近完成
- Phase 1 页面骨架完成（Streamlit 四区布局）
- Phase 2 模版结构读取完成（sidebar 接入真实 RULESET_LAND，差异化 fallback）
- Bug Fix: 右侧保存后中间预览即时更新
- Phase 3 要素系统完成（element_resolver.py，真实字段映射，动态 markdown）
- Phase 4 文档预览完成：
  - 实现 document_service.py：build_node_markdown / build_full_markdown
  - session.preview_mode 字段管理节点/全文模式
  - document_preview.py 支持节点预览 / 全文预览 radio 切换
  - 全文预览 DFS 遍历 template_tree，各节点以 --- 分隔

## 下一步
Phase 5 - fd_reportai_word 适配器
1. 实现 report_adapter.py：调用 fd_reportai_word pipeline 生成 markdown
2. 接入真实文档生成（cover, summary, object_definition, result_usage, attachments）
3. 生成结果写回 session.markdown，触发即时预览更新
4. 更新 `PHASE.md` 记录 Phase 2 收尾结果
