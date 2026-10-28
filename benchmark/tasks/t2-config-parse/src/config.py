"""配置合并：解析结果 + 默认值 + 校验。"""
from parser import parse_text

def build_config(text, defaults=None):
    """解析 + 合并默认值 + 返回最终配置。"""
    parsed = parse_text(text)
    defaults = defaults or {}
    merged = {**parsed, **defaults}
    return merged
