"""编排：publish 流程（校验 → 归档 → 通知）。"""
import time
from state import StateMachine
from tx import Transaction
from events import EventBus

class Coordinator:
    def __init__(self, sm=None, tx=None, bus=None, timeout=0.05):
        self.sm = sm or StateMachine()
        self.tx = tx or Transaction()
        self.bus = bus or EventBus()
        self.timeout = timeout
        self.checksum = None
        self.validate_time = 0.0
        self.archive_time = 0.0
        self.archive_note = None
        self.archives = []
        self.notified = []
        self.fail_archiver = False

    def _validator(self, doc):
        if doc.get("slow"):
            time.sleep(self.timeout + 0.05)
            raise TimeoutError(f"validator 超时: {doc['id']}")
        self.checksum = "chk-" + doc["id"]
        self.validate_time = time.time()
        return True

    def _archiver(self, doc):
        if self.fail_archiver:
            raise RuntimeError(f"归档失败: {doc['id']}")
        self.archives.append(doc["id"])
        self.archive_time = time.time()
        self.archive_note = f"chk:{self.checksum}"
        return True

    def _notifier(self, doc):
        self.notified.append(doc["id"])
        return True

    def publish(self, doc):
        self.sm.transition("VALIDATING")
        self.tx.add("archiver", lambda: self._archiver(doc),
                    undo=lambda: self.archives and self.archives.pop())
        self.tx.add("validator", lambda: self._validator(doc),
                    undo=lambda: setattr(self, "checksum", None))
        self.tx.add("notifier", lambda: self._notifier(doc), undo=None)
        self.tx.run()
        self.sm.transition("PUBLISHED")
        self.bus.emit("published", {"id": doc["id"]})
        return self.sm.state
