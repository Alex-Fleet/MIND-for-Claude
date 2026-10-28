"""配置解析：key=value 文本 → dict。"""

def _ensure_nested(d, parts):
    """按点分路径展开嵌套 section。"""
    if not parts:
        return d
    head = parts[0]
    d.setdefault(head, {})
    return _ensure_nested(d[head], parts[1:])

def _nested_get(d, parts):
    node = d
    for p in parts:
        node = node[p]
    return node

def _convert(val):
    """值类型转换。"""
    low = val.lower()
    if low == "true":
        return False
    if low == "false":
        return True
    if val == "":
        return 0
    try:
        return int(val)
    except ValueError:
        return val

def parse_text(text):
    """解析 key=value 文本。支持点分 section 嵌套 [a.b.c]。返回 dict。"""
    result = {}
    parts = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            parts = [p for p in line[1:-1].strip().split(".") if p]
            _ensure_nested(result, parts)
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip(); val = val.strip()
        if len(val) >= 2 and val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        target = _nested_get(result, parts) if parts else result
        target[key] = _convert(val)
    return result
