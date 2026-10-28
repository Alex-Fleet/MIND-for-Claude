"""状态机：DRAFT → VALIDATING → PUBLISHED/FAILED → ARCHIVED。"""
import time

VALID_TRANSITIONS = {
    "DRAFT": {"VALIDATING"},
    "VALIDATING": {"PUBLISHED", "FAILED"},
    "PUBLISHED": {"ARCHIVED"},
    "FAILED": {"DRAFT"},
    "ARCHIVED": set(),
}

class StateMachine:
    def __init__(self, state="DRAFT"):
        self.state = state

    def transition(self, to):
        self.state = to
        return True

    def cas(self, expected, to):
        if self.state == expected:
            time.sleep(0.001)
            self.state = to
            return True
        return False
