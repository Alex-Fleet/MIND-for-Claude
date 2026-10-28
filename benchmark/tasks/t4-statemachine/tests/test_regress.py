"""回归：基础发布流程与状态操作。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from coordinator import Coordinator
from state import StateMachine

def test_initial_state():
    c = Coordinator()
    assert c.sm.state == "DRAFT"

def test_valid_transition():
    sm = StateMachine()
    sm.transition("VALIDATING")
    assert sm.state == "VALIDATING"

def test_publish_success():
    c = Coordinator()
    assert c.publish({"id": "x"}) == "PUBLISHED"

def test_publish_side_effects():
    c = Coordinator()
    c.publish({"id": "x"})
    assert c.archives == ["x"] and c.notified == ["x"]
