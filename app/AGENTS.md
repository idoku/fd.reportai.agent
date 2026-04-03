# AGENTS.md

> 记录项目长期稳定的目标、架构原则与执行规则。
> 不记录阶段进度、已完成事项或临时断点。
> 执行时必须结合 `PLAN.md`、`ISSUES.md`、`STATE.md` 一起使用。

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
### 执行流程
1. 读取 STATE.md  
   - 确认当前阶段  
   - 确认当前焦点  
   - 确认下一步  
2. 对照 PLAN.md  
   - 仅执行当前 Phase  
   - 不进入后续阶段  
   - 不超出限制条件  
3. 参考 ISSUES.md  
   - 避免已知问题  
   - 解决open的问题
   - 若遇新问题，记录到Later.
4. 执行任务  
   - 优先完成最小闭环  
   - 优先打通主链路  
   - 不做无关优化  
  
### 执行后
1. 更新 STATE.md（覆盖写入）
2. 追加 PHASE.md（记录阶段进展）
3. 如有问题 → 更新 ISSUES.md
