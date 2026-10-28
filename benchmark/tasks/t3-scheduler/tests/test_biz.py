"""业务测试：修完 7 个耦合 bug 后全部通过（网状，见设计文档 T3）。"""
import sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from scheduler import Scheduler

def test_priority_order():  # P1 高优先级先执行
    s = Scheduler(quota=100)
    s.schedule([("low", 1, 10), ("high", 9, 10)])
    assert s.executed[0] == "high", f"高优先级应先执行，实际 {s.executed}"

def test_quota_exact():  # P2 配额边界（=quota 应允许，末位能发出）
    s = Scheduler(quota=20)
    s.schedule([("a", 5, 10), ("b", 5, 10)])
    assert s.used == 20, f"恰好用满配额应允许，实际 {s.used}"

def test_idempotent():  # P3 幂等（同 id 只执行一次）
    s = Scheduler()
    s.execute_idempotent("x")
    s.execute_idempotent("x")
    assert s.execution_count("x") == 1, f"同任务应只执行一次，实际 {s.execution_count('x')}"

def test_concurrent_used():  # P4 并发 used 准确（读-改-写无锁 → 丢更新）
    s = Scheduler(quota=1000)
    barrier = threading.Barrier(10)
    def worker(i):
        barrier.wait()
        s._dispatch(f"t{i}", 10)
    ts = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in ts: t.start()
    for t in ts: t.join()
    assert s.used == 100, f"并发 used 应 100，实际 {s.used}"

def test_no_starvation():  # P5 低优先级不饿死（老化/晋升）
    s = Scheduler(quota=1000, min_priority=3)
    s.schedule([("low", 1, 1), ("low2", 1, 1)])
    assert "low" in s.executed, "低优先级任务不应被永久丢弃（应有老化/晋升）"

def test_retry_backoff():  # P6 重试退避（attempt 大时至少不是 0 延迟）
    s = Scheduler()
    t0 = time.time(); s.retry("x", 5); dt = time.time() - t0
    assert dt >= 0.1, "第5次重试应有退避延迟"

def test_completion_order():  # P7 完成顺序 = 执行完成序（不是提交序）
    s = Scheduler()
    s.schedule([("low", 1, 1), ("high", 9, 1)])
    assert s.finished == ["high", "low"], f"完成顺序应按执行序，实际 {s.finished}"
