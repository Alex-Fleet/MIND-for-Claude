"""业务测试：必须能解析各种畸形的 LLM 输出。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from robust_json import parse

def test_codeblock_wrapped():
    assert parse('```json\n{"a": 1}\n```') == {"a": 1}

def test_trailing_comma():
    assert parse('{"a": 1, "b": 2,}') == {"a": 1, "b": 2}

def test_single_quotes():
    assert parse("{'a': 1, 'b': 'x'}") == {"a": 1, "b": "x"}

def test_surrounding_text():
    assert parse('这是结果：{"a": 1} 请查收') == {"a": 1}

def test_mixed_quotes():
    assert parse("{\"a\": 'x', 'b': \"y\"}") == {"a": "x", "b": "y"}

def test_multiline():
    assert parse('{\n  "a": 1,\n  "b": [1,2,3]\n}') == {"a": 1, "b": [1,2,3]}

def test_empty_raises():
    for bad in ["", "   ", "```\n```"]:
        try:
            parse(bad); assert False, f"应抛 ValueError: {bad!r}"
        except ValueError:
            pass
