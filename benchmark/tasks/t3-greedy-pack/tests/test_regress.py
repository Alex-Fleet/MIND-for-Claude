"""回归测试：基础打包行为。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from packer import pack, MAX_CHARS

def test_empty():
    assert pack([]) == []

def test_single_small():
    packs = pack([("a", "x")])
    assert len(packs) == 1 and packs[0] == [("a", "x")]

def test_ascii_boundary():
    content = "a" * MAX_CHARS
    assert len(pack([("a", content)])[0][0][1]) == MAX_CHARS

def test_all_packs_within_limit():
    files = [(f"f{i}", "c" * 3000) for i in range(10)]
    for pack_ in pack(files):
        total = sum(len(c) for _, c in pack_)
        assert total <= MAX_CHARS
