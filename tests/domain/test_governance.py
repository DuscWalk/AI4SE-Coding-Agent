# tests/domain/test_governance.py
from coding_agent.domain.governance import Governance, Permission, HITLState
from coding_agent.domain.models import Action, ActionType


def test_safe_action_allowed():
    gov = Governance()
    action = Action(type=ActionType.CALL_TOOL, tool_name="read_file", tool_args={"path": "test.py"})
    result = gov.check(action)
    assert result.permission == Permission.ALLOWED


def test_risky_action_needs_confirmation():
    gov = Governance()
    action = Action(type=ActionType.CALL_TOOL, tool_name="write_file", tool_args={"path": "test.py"})
    result = gov.check(action)
    assert result.permission == Permission.NEEDS_CONFIRMATION


def test_dangerous_action_needs_hitl():
    gov = Governance()
    action = Action(type=ActionType.CALL_TOOL, tool_name="run_shell", tool_args={"command": "rm file.txt"})
    result = gov.check(action)
    assert result.permission == Permission.NEEDS_HITL


def test_blocked_command_rm_rf_root():
    gov = Governance()
    action = Action(type=ActionType.CALL_TOOL, tool_name="run_shell", tool_args={"command": "rm -rf /"})
    result = gov.check(action)
    assert result.permission == Permission.BLOCKED


def test_blocked_command_drop_table():
    gov = Governance()
    action = Action(type=ActionType.CALL_TOOL, tool_name="run_shell", tool_args={"command": "DROP TABLE users"})
    result = gov.check(action)
    assert result.permission == Permission.BLOCKED


def test_git_commit_needs_confirmation():
    """git_commit is a RISKY tool, needs user confirmation."""
    gov = Governance()
    action = Action(type=ActionType.CALL_TOOL, tool_name="git_commit", tool_args={"message": "x"})
    result = gov.check(action)
    assert result.permission == Permission.NEEDS_CONFIRMATION


def test_blocked_command_format_c():
    gov = Governance()
    action = Action(type=ActionType.CALL_TOOL, tool_name="run_shell", tool_args={"command": "format C:"})
    result = gov.check(action)
    assert result.permission == Permission.BLOCKED


def test_unknown_tool_blocked():
    gov = Governance()
    action = Action(type=ActionType.CALL_TOOL, tool_name="delete_everything", tool_args={})
    result = gov.check(action)
    assert result.permission == Permission.BLOCKED


def test_done_action_allowed():
    gov = Governance()
    action = Action(type=ActionType.DONE, thought="task complete")
    result = gov.check(action)
    assert result.permission == Permission.ALLOWED


def test_hitl_state_approve():
    state = HITLState()
    state.request("run dangerous command?")
    result = state.approve()
    assert result is True
    assert state.is_resolved() is True


def test_hitl_state_deny():
    state = HITLState()
    state.request("run dangerous command?")
    result = state.deny()
    assert result is False
    assert state.is_resolved() is True