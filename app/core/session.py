"""
session.py — ReportSession 业务状态模型。

纯 Python dataclass，不依赖 Streamlit 或任何 UI 框架。
Phase 2：template_tree 由 config_loader 填充（优先真实数据，fallback mock）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy

from app.core.mock_data import MOCK_FIELDS, MOCK_MARKDOWN


@dataclass
class ReportSession:
    """全局报告会话状态，挂载在 st.session_state["report_session"]。"""

    # 模版节点树，由 config_loader 填充（{key, title, children}）
    template_tree: list[dict] = field(default_factory=list)

    # 当前选中的节点 key
    selected_node: str | None = None

    # 节点 key → 字段列表 [{key, label, value}]
    fields: dict[str, list[dict]] = field(default_factory=dict)

    # 节点 key → markdown 预览文本（Phase 5 起由 AI 生成替换）
    markdown: dict[str, str] = field(default_factory=dict)

    # 聊天记录 [{role: "user"|"assistant", content: str}]
    chat_history: list[dict] = field(default_factory=list)

    def get_current_fields(self) -> list[dict]:
        """返回当前节点的字段列表，未选中时返回空列表。"""
        if self.selected_node is None:
            return []
        return self.fields.get(self.selected_node, [])

    def get_current_markdown(self) -> str:
        """返回当前节点的 markdown 预览，未选中时返回提示文字。"""
        if self.selected_node is None:
            return "_请在左侧选择一个节点以预览内容_"
        return self.markdown.get(self.selected_node, "_暂无预览内容_")

    def update_field(self, field_key: str, value: str) -> None:
        """更新当前节点中指定字段的值。"""
        if self.selected_node is None:
            return
        for f in self.fields.get(self.selected_node, []):
            if f["key"] == field_key:
                f["value"] = value
                return

    def rebuild_preview_from_fields(self, node_key: str | None = None) -> None:
        """
        从当前节点的字段值重新生成 markdown 预览表格。
        Phase 5 起此方法被 AI 生成结果替换。
        """
        key = node_key or self.selected_node
        if key is None:
            return
        fields = self.fields.get(key, [])
        if not fields:
            self.markdown[key] = "_暂无字段内容_"
            return
        lines = [f"## {self._node_title(key)}", "", "| 字段 | 值 |", "|------|----|"]
        for f in fields:
            lines.append(f"| {f['label']} | {f['value']} |")
        self.markdown[key] = "\n".join(lines)

    def _node_title(self, node_key: str) -> str:
        """从 template_tree 中查找节点标题，找不到时返回 key。"""
        def _search(nodes: list[dict]) -> str | None:
            for n in nodes:
                if n["key"] == node_key:
                    return n["title"]
                found = _search(n.get("children", []))
                if found:
                    return found
            return None
        return _search(self.template_tree) or node_key

    def add_chat_message(self, role: str, content: str) -> None:
        """追加一条聊天消息。"""
        self.chat_history.append({"role": role, "content": content})


def init_session() -> ReportSession:
    """创建并返回初始 ReportSession。Phase 2：template_tree 来自 config_loader。"""
    from app.core.config_loader import load_template_nodes  # noqa: PLC0415

    tree = load_template_nodes()
    first_key = tree[0]["key"] if tree else None
    return ReportSession(
        template_tree=tree,
        selected_node=first_key,
        fields=deepcopy(MOCK_FIELDS),
        markdown=deepcopy(MOCK_MARKDOWN),
        chat_history=[],
    )
