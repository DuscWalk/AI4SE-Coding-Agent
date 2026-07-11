# tests/infrastructure/test_llm_provider.py
import pytest
from coding_agent.infrastructure.llm_provider import (
    ScriptedMockLLM, RuleBasedMockLLM, LLMResponse, ToolCall
)
from coding_agent.domain.models import Message


def test_scripted_mock_returns_preset_responses():
    responses = [
        LLMResponse(text="step 1", tool_calls=[
            ToolCall(name="read_file", arguments={"path": "test.py"})
        ]),
        LLMResponse(text="done", tool_calls=[]),
    ]
    llm = ScriptedMockLLM(responses)
    msgs = [Message(role="user", content="task")]
    tools = [{"name": "read_file", "description": "read a file"}]

    r1 = llm.chat(msgs, tools)
    assert r1.text == "step 1"
    assert len(r1.tool_calls) == 1
    assert r1.tool_calls[0].name == "read_file"

    r2 = llm.chat(msgs, tools)
    assert r2.text == "done"
    assert len(r2.tool_calls) == 0


def test_scripted_mock_raises_when_exhausted():
    llm = ScriptedMockLLM([LLMResponse(text="only one", tool_calls=[])])
    llm.chat([], [])
    with pytest.raises(IndexError):
        llm.chat([], [])


def test_rule_based_mock_matches_pattern():
    rules = [
        (lambda msgs, tools: "error" in msgs[-1].content,
         LLMResponse(text="fixing", tool_calls=[
             ToolCall(name="write_file", arguments={"path": "test.py", "content": "fixed"})
         ])),
        (lambda msgs, tools: True,
         LLMResponse(text="done", tool_calls=[])),
    ]
    llm = RuleBasedMockLLM(rules)

    r1 = llm.chat([Message(role="user", content="error in test.py")], [])
    assert r1.text == "fixing"
    assert r1.tool_calls[0].name == "write_file"

    r2 = llm.chat([Message(role="user", content="all good")], [])
    assert r2.text == "done"


def test_llm_response_tool_calls():
    tc = ToolCall(name="run_shell", arguments={"command": "pytest"})
    assert tc.name == "run_shell"
    assert tc.arguments == {"command": "pytest"}