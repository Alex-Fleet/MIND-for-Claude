"""回归：基础解析（正确行为：数字转 int、布尔判真）。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from run import load_config

def test_basic_kv():
    r = load_config("a=1\nb=2\n")
    assert r["a"] == 1 and r["b"] == 2

def test_comments():
    r = load_config("# comment\na=1\n")
    assert r["a"] == 1

def test_empty():
    assert load_config("") == {}

def test_section_kv():
    r = load_config("[s]\nk=v\n")
    assert r["s"]["k"] == "v"
