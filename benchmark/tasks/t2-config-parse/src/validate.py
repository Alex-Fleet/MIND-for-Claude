"""校验：值类型/范围检查。"""
def validate(config):
    """应校验: 端口范围、枚举值、必填项。"""
    for key, val in config.items():
        if isinstance(val, int) and val < 0:
            raise ValueError(f"{key} 不能为负数: {val}")
    return config
