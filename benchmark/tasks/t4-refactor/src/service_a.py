"""服务 A — 用户视图渲染（依赖 format_entry）。"""
from core import format_entry

def render_user(doc: dict) -> str:
    return format_entry(doc["name"], doc["tags"])
