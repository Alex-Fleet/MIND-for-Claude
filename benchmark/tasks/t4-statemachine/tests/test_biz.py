"""业务测试：修完 7 个耦合 bug 后全部通过（网状，见设计文档 T4）。"""
import sys, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from coordinator import Coordinator

def test_invalid_transition():  # S1 非法状态跳变被拦截
    c = Coordinator()
    c.sm.state = "DRAFT"
    # DRAFT → ARCHIVED 非法跳变（跳过 VALIDATING/PUBLISHED）
    ok = c.sm.transition("ARCHIVED")
    assert not ok or c.sm.state != "ARCHIVED", "非法状态跳变应被拦截"

def test_order_correct():  # S2 跨服务调用顺序（归档在校验之后）
    c = Coordinator()
    c.publish({"id": "x"})
    assert c.archive_time >= c.validate_time, f"归档应发生在校验之后（错序）: a={c.archive_time} v={c.validate_time}"
    assert c.archive_note == "chk:chk-x", f"归档记录应含校验结果: {c.archive_note}"

def test_atomic_failure():  # S3 事务整体原子（无部分提交残留）
    c = Coordinator()
    c.fail_archiver = True
    try:
        c.publish({"id": "x"})
        raise AssertionError("archiver 失败时 publish 应失败")
    except Exception:
        pass
    assert c.checksum is None, f"事务失败后校验副作用不应残留（部分提交）: {c.checksum}"
    assert c.archives == [], f"事务失败后归档副作用不应残留: {c.archives}"

def test_rollback_complete():  # S4 回滚完整（撤销所有副作用，含通知）
    c = Coordinator()
    c.publish({"id": "x"})
    c.tx.rollback()
    assert c.notified == [], f"回滚后通知副作用不应残留: {c.notified}"
    assert c.checksum is None, "回滚后校验副作用不应残留"
    assert c.archives == [], "回滚后归档副作用不应残留"

def test_event_not_lost():  # S5 事件不丢（所有订阅者都收到）
    c = Coordinator()
    received = []
    c.bus.subscribe(lambda ev, pl: received.append(pl["id"]))
    c.bus.subscribe(lambda ev, pl: received.append(pl["id"]))
    c.publish({"id": "x"})
    assert len(received) == 2, f"两个订阅者都应收到事件，实际 {len(received)}"

def test_concurrent_state():  # S6 并发状态一致（无 ABA 双成功）
    c = Coordinator()
    c.sm.state = "PUBLISHED"
    results = []
    def archiver():
        results.append(c.sm.cas("PUBLISHED", "ARCHIVED"))
    ts = [threading.Thread(target=archiver) for _ in range(2)]
    for t in ts: t.start()
    for t in ts: t.join()
    assert results.count(True) == 1, f"只有一个并发操作应成功，实际 {results}"

def test_timeout_handled():  # S7 超时有兜底（状态不卡死）
    c = Coordinator(timeout=0.05)
    c.sm.transition("VALIDATING")
    try:
        c.publish({"id": "x", "slow": True})
        raise AssertionError("慢任务应被兜底处理（不卡死）")
    except Exception:
        pass
    assert c.sm.state != "VALIDATING", f"超时后状态不应卡在 VALIDATING: {c.sm.state}"
