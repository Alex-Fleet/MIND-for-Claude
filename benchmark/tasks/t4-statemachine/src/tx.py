"""事务管理。"""

class Transaction:
    def __init__(self):
        self._steps = []

    def add(self, name, do, undo=None):
        self._steps.append({"name": name, "do": do, "undo": undo})

    def run(self):
        for s in self._steps:
            s["do"]()
        return True

    def rollback(self):
        for s in reversed(self._steps):
            if s["undo"]:
                s["undo"]()
        return True
