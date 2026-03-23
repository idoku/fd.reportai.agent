from __future__ import annotations

from dataclasses import dataclass, field

from .results import BlockResult


@dataclass(slots=True)
class ReportSectionDocument:
    key: str
    title: str
    blocks: list[BlockResult] = field(default_factory=list)
    children: list["ReportSectionDocument"] = field(default_factory=list)
    options: dict[str, object] = field(default_factory=dict)

    def __getitem__(self, key: str):
        if key == "key":
            return self.key
        if key == "title":
            return self.title
        if key == "blocks":
            return self.blocks
        if key == "children":
            return self.children
        if key == "options":
            return self.options
        if key == "content":
            if not self.blocks:
                return None
            content = self.blocks[0].content
            if (
                isinstance(content, dict)
                and content.get("type") == "rich_text"
                and "text" in content
            ):
                return content.get("text")
            return content
        raise KeyError(key)


@dataclass(slots=True)
class ReportDocument:
    title: str
    template_key: str
    template_version: str
    sections: list[ReportSectionDocument] = field(default_factory=list)
    blocked_items: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    def __getitem__(self, key: str):
        if key == "title":
            return self.title
        if key == "sections":
            return self.sections
        if key == "blocked_items":
            return self.blocked_items
        if key == "metadata":
            return self.metadata
        if key == "template_key":
            return self.template_key
        if key == "template_version":
            return self.template_version
        raise KeyError(key)
