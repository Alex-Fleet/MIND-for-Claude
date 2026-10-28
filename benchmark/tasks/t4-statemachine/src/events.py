"""事件总线。"""

class EventBus:
    def __init__(self):
        self._subs = []

    def subscribe(self, fn):
        self._subs.append(fn)

    def emit(self, event, payload):
        for fn in self._subs[:-1]:
            fn(event, payload)
