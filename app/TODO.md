
---

# ⚙️ 二、TODO.md（任务执行清单）

👉 放在项目根目录：`TODO.md`

```markdown
# TODO.md

## 当前阶段：Phase 1 - 页面骨架

---

## Step 1：初始化项目

- [ ] 创建项目目录结构
- [ ] 创建 app.py
- [ ] 创建 requirements.txt
- [ ] 安装依赖（streamlit）

---

## Step 2：实现页面基础布局

目标：四区布局

- [ ] 左侧 sidebar
- [ ] 中间 preview
- [ ] 右侧 element panel
- [ ] 下方 chat panel

---

## Step 3：实现 mock 数据

- [ ] mock 模版树
- [ ] mock 字段
- [ ] mock markdown

---

## Step 4：实现 UI 模块

### sidebar_tree.py
- [ ] 渲染节点列表
- [ ] 支持选择节点

### element_panel.py
- [ ] 渲染字段表单
- [ ] 支持输入修改

### document_preview.py
- [ ] 渲染 markdown

### chat_panel.py
- [ ] 输入框
- [ ] 显示聊天记录
- [ ] 文件上传按钮

---

## 验收（Phase 1）

- [ ] 页面可以运行
- [ ] 能切换节点
- [ ] 能编辑字段
- [ ] 能看到预览
- [ ] 能输入聊天

---

# Phase 2：模版结构读取

- [ ] 实现 config_loader.py
- [ ] 读取 fd_reportai_word 配置
- [ ] 转换为 TemplateNode
- [ ] 替换 mock 数据

---

# Phase 3：要素系统

- [ ] 实现 element_resolver.py
- [ ] 节点 -> 字段映射
- [ ] 字段编辑保存到 session
- [ ] 页面刷新不丢失

---

# Phase 4：文档预览

- [ ] 实现 document_service.py
- [ ] 当前节点 markdown
- [ ] 全文 markdown
- [ ] 支持切换

---

# Phase 5：接入 fd_reportai_word

- [ ] 实现 reportai_word_adapter.py
- [ ] 转换 session -> pipeline 输入
- [ ] 生成 markdown
- [ ] 写回 session

---

# Phase 6：LangGraph 对话

- [ ] 实现 state.py
- [ ] 实现 router.py
- [ ] 实现 nodes.py
- [ ] 实现 workflow.py
- [ ] 接入 chat_panel

支持：

- [ ] 修改字段
- [ ] 生成节点
- [ ] 生成全文

---

# Phase 7：文件上传

- [ ] 实现 file_parser.py
- [ ] 保存文件
- [ ] 提取文本（txt/md/docx）
- [ ] pdf 先不解析

---

# Phase 8：导出 Word

- [ ] 实现 export_service.py
- [ ] markdown -> docx
- [ ] 下载按钮

---

# 最终验收

- [ ] 左侧模版树
- [ ] 右侧字段编辑
- [ ] 中间文档预览
- [ ] 下方对话
- [ ] docx导出
- [ ] 对话驱动修改字段