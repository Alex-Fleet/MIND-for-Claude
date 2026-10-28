"""服务 B — 报告渲染（依赖 format_entry）。"""
from core import format_entry

def render_report(docs: list[dict]) -> list[str]:
    return [format_entry(d["name"], d["tags"]) for d in docs]
