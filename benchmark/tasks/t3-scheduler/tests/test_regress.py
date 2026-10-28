"""回归：基础调度。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from scheduler import Scheduler

def test_basic_schedule():
    s = Scheduler(quota=40)
    s.schedule([("a", 1, 10), ("b", 1, 10), ("c", 1, 10)])
    assert len(s.executed) == 3

def test_quota_limit():
    s = Scheduler(quota=15)
    s.schedule([("a", 1, 10), ("b", 1, 10)])
    assert s.used <= 15

def test_results():
    s = Scheduler()
    s.schedule([("a", 1, 10)])
    assert s.results["a"] == "done-a"
