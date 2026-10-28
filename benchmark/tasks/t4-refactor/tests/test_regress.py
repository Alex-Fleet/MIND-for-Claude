"""回归测试：现有调用方行为不变。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import core, service_a, service_b, service_c

def test_core_default():
    assert core.format_entry("d", ["x", "y"]) == "d: x, y"

def test_service_a():
    assert service_a.render_user({"name": "u", "tags": ["t1"]}) == "u: t1"

def test_service_c():
    docs = [{"name": "l1", "tags": ["x", "y"]}]
    assert service_c.render_log(docs) == ["l1: x, y"]

def test_service_b():
    docs = [{"name": "d1", "tags": ["a"]}, {"name": "d2", "tags": ["b", "c"]}]
    assert service_b.render_report(docs) == ["d1: a", "d2: b, c"]
