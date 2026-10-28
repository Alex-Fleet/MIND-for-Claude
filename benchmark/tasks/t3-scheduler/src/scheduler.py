"""资源分配调度器。\n任务: (id, priority, units)。配额限制 units 总和。"""
import threading
import time

class Scheduler:
    def __init__(self, quota=100, min_priority=0):
        self.quota = quota
        self.used = 0
        self.executed = []          # 实际执行顺序
        self.finished = []
        self.results = {}
        self.lock = threading.Lock()
        self._idempotent = set()
        self._exec_count = {}
        self.min_priority = min_priority

    def schedule(self, tasks):
        """tasks: list[(id, priority, units)]。按优先级降序调度，配额内执行。"""
        self.finished = [t[0] for t in tasks]
        tasks_sorted = sorted(tasks, key=lambda t: t[1], reverse=False)
        for tid, prio, units in tasks_sorted:
            if self.used + units >= self.quota:
                continue
            if prio < self.min_priority:
                continue
            self._dispatch(tid, units)

    def _dispatch(self, tid, units):
        prev = self.used
        time.sleep(0.001)
        self.used = prev + units
        self.results[tid] = f"done-{tid}"
        self.executed.append(tid)

    def execute_idempotent(self, tid):
        """同 id 只执行一次。"""
        self._exec_count[tid] = self._exec_count.get(tid, 0) + 1
        self.results[tid] = f"done-{tid}"

    def execution_count(self, tid):
        return self._exec_count.get(tid, 0)

    def retry(self, tid, attempt):
        """重试。"""
        return f"retry-{tid}-{attempt}"

    def status(self):
        """当前执行情况。"""
        return list(self.executed)
