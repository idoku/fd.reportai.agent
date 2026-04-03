# AGENTS.md

## 项目目标

实现一个基于 Streamlit 的交互式报告生成系统（Report Studio），支持：

- 模版结构浏览
- 节点要素编辑
- 文档结构预览
- 对话驱动修改
- 文档导出（docx）

---

## 技术栈

- UI：Streamlit
- 编排：LangGraph / LangChain
- 文档生成：fd_reportai_word
- 导出：pypandoc

---

## 核心原则

1. 先保证“最小可运行闭环”，再扩展功能
2. 所有逻辑必须围绕 ReportSession 状态展开
3. 不允许 UI 直接调用复杂逻辑，必须通过 core/service 层
4. 所有外部系统（fd_reportai_word）必须通过 adapter 层访问
5. 所有对话处理必须走 graph 层（LangGraph）

---

## 模块职责

### app.py
- 入口
- 页面布局
- 调用 UI 模块
- 挂载 session

### core/
- 纯业务逻辑
- 不依赖 UI
- 不依赖 LangGraph

### ui/
- 只负责展示
- 不做业务逻辑

### graph/
- 负责对话解析与决策
- 修改 session

### adapters/
- 适配外部系统
- fd_reportai_word
- 文件解析

---

## 开发顺序（必须严格执行）

1. 页面骨架（mock数据）
2. 模版结构读取
3. 节点要素编辑
4. 文档预览
5. 接入 fd_reportai_word
6. 对话能力（LangGraph）
7. 文件上传
8. 导出 docx

---

## 禁止事项

❌ 不允许一开始实现完整 AI 流程  
❌ 不允许跳过 Phase 直接实现后面功能  
❌ 不允许 UI 和业务逻辑混写  
❌ 不允许直接在 UI 中调用 LLM  

---

## 输出规范（每个任务完成后）

必须输出：

1. 修改文件列表
2. 核心实现说明
3. 如何运行
4. 如何验证

---

## 状态管理

统一使用：

```python
st.session_state["report_session"]