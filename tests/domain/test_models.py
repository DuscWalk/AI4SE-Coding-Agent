import pytest
from coding_agent.domain.models import (
    Action, ActionType, ActionResult, Message, SensorReport,
    SensorFailure, FailureCategory, FailureSeverity, MemoryEntry
)


def test_action_creation():
    action = Action(
        type=ActionType.CALL_TOOL,
        tool_name="read_file",
        tool_args={"path": "test.py"},
        thought="reading the file"
    )
    assert action.type == ActionType.CALL_TOOL
    assert action.tool_name == "read_file"


def test_action_done():
    action = Action(type=ActionType.DONE, thought="done")
    assert action.type == ActionType.DONE
    assert action.tool_name is None


def test_action_result_success():
    result = ActionResult(success=True, output="file content", changed_files=[])
    assert result.success is True
    assert result.error is None


def test_action_result_failure():
    result = ActionResult(success=False, output="", error="file not found", changed_files=[])
    assert result.success is False
    assert result.error == "file not found"


def test_message_creation():
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"


def test_sensor_failure():
    failure = SensorFailure(
        file_path="test.py",
        line=10,
        severity=FailureSeverity.ERROR,
        category=FailureCategory.SYNTAX_ERROR,
        message="invalid syntax",
        raw_output="SyntaxError: invalid syntax"
    )
    assert failure.category == FailureCategory.SYNTAX_ERROR
    assert failure.severity == FailureSeverity.ERROR


def test_sensor_report():
    failure = SensorFailure(
        file_path="test.py", line=1, severity=FailureSeverity.ERROR,
        category=FailureCategory.SYNTAX_ERROR, message="err", raw_output="err"
    )
    report = SensorReport(sensor_name="syntax", passed=False, failures=[failure], duration_ms=100)
    assert report.passed is False
    assert len(report.failures) == 1


def test_memory_entry():
    import datetime
    entry = MemoryEntry(
        id="abc-123", content="project uses pytest",
        timestamp=datetime.datetime.now(), type="long_term"
    )
    assert entry.id == "abc-123"
    assert entry.type == "long_term"