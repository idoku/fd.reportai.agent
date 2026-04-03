# AGENTS.md

## 项目目标

实现一个基于 Streamlit 的交互式报告生成系统（Report Studio），支持：

- 模版结构浏览（左侧）
- 节点要素编辑（右侧）
- 文档结构与内容预览（中间）
- 对话驱动修改（底部）
- 导出 Word 文档（docx）

---

## 技术栈

- UI：Streamlit
- 编排：LangGraph / LangChain
- 文档生成：fd_reportai_word
- 导出：pypandoc

---

## 核心架构原则

1. 单一状态源：所有数据必须存储在 `ReportSession`
2. UI 与业务分离：UI 不允许包含业务逻辑
3. 分层结构：
   - core：业务逻辑
   - ui：展示层
   - graph：对话编排
   - adapters：外部系统适配
4. 所有对话必须通过 graph 层处理
5. 所有外部调用必须通过 adapter 层

---

## 状态管理

唯一状态入口：

```python
st.session_state["report_session"]
```

## 项目文档约定
- AGENTS.md：项目目标与架构规则（长期稳定）
- PLAN.md：当前阶段任务与目标
- ISSUES.md：问题、风险、阻塞
- PHASE.md：阶段进展与产出（历史）
- STATE.md：当前执行状态（可恢复上下文）

## 执行规则
- 按 PLAN 推进任务
- 参考 ISSUES 避免已知问题，发现新问题及时记录
- 所有阶段性结果写入 PHASE,
- 始终基于 STATE 继续执行，并在结束后更新
- 每次任务完成后，更新 STATE.md，只保留当前阶段、当前焦点、当前断点、最近完成、下一步
- PHASE.md 按阶段追加记录，使用固定模板：时间 / 阶段目标 / 主要变更 / 阶段产出 / 遗留问题；只追加新阶段，不改写旧阶段

## STATE 约束
- 当前阶段 / 焦点
- 当前阻塞
- 最近完成
- 下一步
不记录历史（历史统一写入 PHASE.md）