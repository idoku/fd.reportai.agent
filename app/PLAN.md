# PLAN.md

## 当前阶段：Phase 2 - 模版结构读取

---

## Phase 1（已完成）

基础骨架已完成，包括：

- 页面结构（四区布局）
- mock 数据
- session 初始化

---

## Phase 2：模版结构读取（当前执行）

### 目标

将左侧 mock 模版树替换为 fd_reportai_word 的真实配置

---

### 执行步骤（按顺序）

1. 实现 `core/config_loader.py`
2. 读取 fd_reportai_word 配置
3. 提取 section / 节点结构
4. 转换为 TemplateNode
5. 替换 sidebar_tree 的 mock 数据
6. 保留 fallback（mock）

---

### 限制

- 不实现字段映射（Phase 3）
- 不引入 LangGraph
- 不修改 UI 布局
- 不修改 chat_panel

---

### 验收标准

- 左侧展示真实模版结构
- 点击节点可切换
- 页面无报错
- mock fallback 可用

---

## 后续阶段（预览）

### Phase 3：要素系统
- element_resolver
- 节点字段映射
- 字段写入 session

### Phase 4：文档预览
- markdown 渲染
- 节点 / 全文切换

### Phase 5：文档生成
- 接入 fd_reportai_word
- 生成 markdown

### Phase 6：对话能力
- LangGraph
- 修改字段
- 生成内容

### Phase 7：文件上传
- file_parser
- 文件存储

### Phase 8：导出
- pypandoc
- docx 下载

---

## 最终验收

- 可选节点
- 可编辑字段
- 可生成文档
- 可导出 docx
- 可对话修改