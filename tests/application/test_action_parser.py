# tests/application/test_action_parser.py
from __future__ import annotations

from coding_agent.application.action_parser import ActionParser
from coding_agent.infrastructure.llm_provider import LLMResponse, ToolCall
from coding_agent.domain.models import ActionType


def test_parse_tool_call():
    response = LLMResponse(
        text="reading the file",
        tool_calls=[ToolCall(name="read_file", arguments={"path": "test.py"})],
    )
    action = ActionParser.parse(response)
    assert action is not None
    assert action.type == ActionType.CALL_TOOL
    assert action.tool_name == "read_file"
    assert action.tool_args == {"path": "test.py"}
    assert action.thought == "reading the file"


def test_parse_multiple_tool_calls_uses_first():
    response = LLMResponse(
        text="doing multiple things",
        tool_calls=[
            ToolCall(name="read_file", arguments={"path": "a.py"}),
            ToolCall(name="write_file", arguments={"path": "b.py", "content": "x"}),
        ],
    )
    action = ActionParser.parse(response)
    assert action is not None
    assert action.type == ActionType.CALL_TOOL
    assert action.tool_name == "read_file"


def test_parse_json_action():
    response = LLMResponse(
        text='```json\n{"tool_name": "write_file", "tool_args": {"path": "x.py", "content": "hello"}, "thought": "writing"}\n```'
    )
    action = ActionParser.parse(response)
    assert action is not None
    assert action.tool_name == "write_file"
    assert action.tool_args == {"path": "x.py", "content": "hello"}
    assert action.thought == "writing"


def test_parse_json_action_with_action_field():
    response = LLMResponse(
        text='```json\n{"action": "done", "thought": "all done"}\n```'
    )
    action = ActionParser.parse(response)
    assert action is not None
    assert action.type == ActionType.DONE
    assert action.thought == "all done"


def test_parse_json_action_take_note():
    response = LLMResponse(
        text='```json\n{"type": "take_note", "note": "remember this", "thought": "noting"}\n```'
    )
    action = ActionParser.parse(response)
    assert action is not None
    assert action.type == ActionType.TAKE_NOTE
    assert action.note == "remember this"


def test_parse_raw_json():
    response = LLMResponse(
        text='{"tool_name": "read_file", "tool_args": {"path": "f.py"}, "thought": "reading"}'
    )
    action = ActionParser.parse(response)
    assert action is not None
    assert action.type == ActionType.CALL_TOOL
    assert action.tool_name == "read_file"


def test_parse_done():
    response = LLMResponse(text="Task complete. DONE.")
    action = ActionParser.parse(response)
    assert action is not None
    assert action.type == ActionType.DONE


def test_parse_invalid_text():
    response = LLMResponse(text="just some random text")
    action = ActionParser.parse(response)
    assert action is None


def test_parse_invalid_json_fallback():
    response = LLMResponse(
        text='```json\n{invalid json content}\n```'
    )
    action = ActionParser.parse(response)
    assert action is None