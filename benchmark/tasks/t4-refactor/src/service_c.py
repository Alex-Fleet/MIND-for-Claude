"""服务 C — 日志渲染（依赖 format_entry，用默认逗号分隔）。"""
from core import format_entry

def render_log(docs: list[dict]) -> list[str]:
    return [format_entry(d["name"], d["tags"]) for d in docs]
