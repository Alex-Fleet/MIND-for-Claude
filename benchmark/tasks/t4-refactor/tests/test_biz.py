"""业务测试：format_entry 支持 separator 参数（重构需求）。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import core

def test_separator_parameter():
    # 需求: format_entry(name, tags, separator=", ") 支持自定义分隔符
    r = core.format_entry("doc", ["a", "b"], separator="; ")
    assert r == "doc: a; b", f"应支持 separator，实际: {r!r}"

def test_separator_default_comma():
    r = core.format_entry("doc", ["a", "b"])
    assert r == "doc: a, b"
