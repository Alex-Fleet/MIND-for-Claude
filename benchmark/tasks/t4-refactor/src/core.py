"""核心模块 — 条目格式化接口。

format_entry 支持可选 separator 参数（默认 ', '），
调用方可指定自定义分隔符；默认行为与旧版一致（逗号分隔），
现有调用方（service_a / service_b / service_c）不受影响。
"""
def format_entry(name: str, tags: list[str], separator: str = ", ") -> str:
    """格式化一条目。默认用逗号分隔，可通过 separator 指定自定义分隔符。"""
    return f"{name}: {separator.join(tags)}"
