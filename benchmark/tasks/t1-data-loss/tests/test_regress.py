"""回归测试：基础功能。"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from store import Store

def _s(tmp): return Store(str(Path(tmp)))

def test_add_get():
    with tempfile.TemporaryDirectory() as tmp:
        s=_s(tmp); s.add("a","hello"); assert s.get("a")=="hello"

def test_add_overwrite():
    with tempfile.TemporaryDirectory() as tmp:
        s=_s(tmp); s.add("a","v1"); s.add("a","v2"); assert s.get("a")=="v2"

def test_delete_missing():
    with tempfile.TemporaryDirectory() as tmp:
        s=_s(tmp)
        try: s.get("无"); assert False
        except KeyError: pass
