# STATE.md

## 当前阶段
Phase 2 - 模版结构读取

## 当前焦点
将左侧 mock 模版树替换为 fd_reportai_word 的真实配置

## 当前断点
- 尚未实现 core/config_loader.py
- 尚未接入 fd_reportai_word 配置读取
- 未完成 section / 节点结构提取
- 未完成 TemplateNode 转换
- sidebar_tree 仍使用 mock 数据

## 最近完成
- Phase 1 页面骨架完成
- Streamlit 四区布局完成
- mock 模版树已接入
- session 初始化完成
- 节点切换能力已实现
- mock 字段编辑已接入
- markdown 预览已接入
- chat panel 已接入
- 文件上传 UI 已接入

## 下一步
1. 实现 core/config_loader.py
2. 读取 fd_reportai_word 配置
3. 提取 section / 节点结构
4. 转换为 TemplateNode
5. 替换 sidebar_tree 的 mock 数据
6. 保留 fallback（mock）