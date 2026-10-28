"""入口：文本 + 默认值 → 最终配置。"""
from config import build_config
from validate import validate

def load_config(text, defaults=None, validate_=True):
    cfg = build_config(text, defaults)
    if validate_:
        cfg = validate(cfg)
    return cfg
