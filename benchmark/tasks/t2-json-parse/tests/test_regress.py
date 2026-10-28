"""回归测试：标准 JSON 解析行为不变。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from robust_json import parse

def test_standard_object():
    assert parse('{"name": "claude", "age": 30}') == {"name": "claude", "age": 30}

def test_nested():
    assert parse('{"a": {"b": [1, {"c": null}]}}') == {"a": {"b": [1, {"c": None}]}}

def test_scalars():
    assert parse('{"n": 3.14, "ok": true, "s": "hi"}') == {"n": 3.14, "ok": True, "s": "hi"}

def test_invalid_raises():
    try:
        parse('not json at all'); assert False
    except ValueError:
        pass
