# tests/application/test_agent_loop.py
"""Tests for AgentLoop main loop orchestration."""
from __future__ import annotations

import tempfile
from coding_agent.application.agent_loop import AgentLoop
from coding_agent.infrastructure.llm_provider import ScriptedMockLLM, LLMResponse, ToolCall
from coding_agent.domain.tool_manager import ToolManager, ToolDef, ToolPermission
from coding_agent.domain.governance import Governance
from coding_agent.domain.feedback.pipeline import FeedbackPipeline
from coding_agent.domain.feedback.sensors import SyntaxSensor
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.feedback.engine import CorrectionEngine
from coding_agent.application.action_parser import ActionParser
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.memory import MemoryManager
from coding_agent.infrastructure.vector_store import InMemoryVectorStore
from coding_agent.domain.config import Config


def make_harness(responses, tmpdir):
    """Create a fully wired AgentLoop harness with ScriptedMockLLM."""
    llm = ScriptedMockLLM(responses)
    tm = ToolManager()
    tm.register(ToolDef("echo", "echo back", {}, ToolPermission.SAFE,
                        lambda a: a.get("msg", "")))
    governance = Governance()
    pipeline = FeedbackPipeline(
        sensors=[SyntaxSensor()],
        classifier=FailureClassifier(),
        engine=CorrectionEngine(max_retries=3),
    )
    parser = ActionParser()
    session_mgr = SessionManager(tmpdir)
    memory = MemoryManager(InMemoryVectorStore())
    config = Config(max_steps=10)
    return AgentLoop(llm, tm, governance, pipeline, parser, session_mgr, memory, config)


def test_agent_completes_with_done():
    """Agent should return success=True when LLM responds with DONE."""
    responses = [
        LLMResponse(text="let me echo", tool_calls=[
            ToolCall(name="echo", arguments={"msg": "hello"})
        ]),
        LLMResponse(text="all done", tool_calls=[]),
    ]
    with tempfile.TemporaryDirectory() as td:
        loop = make_harness(responses, td)
        result = loop.run("say hello")
        assert result.success is True
        assert result.answer == "all done"


def test_agent_run_reuses_existing_session() -> None:
    responses = [LLMResponse(text="done", tool_calls=[])]
    with tempfile.TemporaryDirectory() as td:
        loop = make_harness(responses, td)
        session = loop.session_manager.create("existing task")

        result = loop.run("existing task", session_id=session.id)

        sessions = loop.session_manager.list_all()
        assert len(sessions) == 1
        assert sessions[0].id == session.id
        assert sessions[0].result == result


def test_agent_stops_at_max_steps():
    """Agent should return failure when max_steps is exceeded."""
    config = Config(max_steps=2)
    responses = [
        LLMResponse(text="step 1", tool_calls=[
            ToolCall(name="echo", arguments={"msg": "x"})
        ]),
        LLMResponse(text="step 2", tool_calls=[
            ToolCall(name="echo", arguments={"msg": "x"})
        ]),
        LLMResponse(text="step 3", tool_calls=[
            ToolCall(name="echo", arguments={"msg": "x"})
        ]),
    ]
    llm = ScriptedMockLLM(responses)
    tm = ToolManager()
    tm.register(ToolDef("echo", "echo", {}, ToolPermission.SAFE,
                        lambda a: a.get("msg", "")))

    with tempfile.TemporaryDirectory() as td:
        loop = AgentLoop(
            llm, tm, Governance(),
            FeedbackPipeline([SyntaxSensor()], FailureClassifier(), CorrectionEngine()),
            ActionParser(), SessionManager(td),
            MemoryManager(InMemoryVectorStore()), config,
        )
        result = loop.run("task")
        assert result.success is False
        assert "max steps" in result.error.lower()


def test_agent_blocked_by_governance():
    """Agent should continue after governance blocks a dangerous action."""
    responses = [
        LLMResponse(text="dangerous", tool_calls=[
            ToolCall(name="echo", arguments={"command": "rm -rf /"})
        ]),
        LLMResponse(text="ok fine", tool_calls=[
            ToolCall(name="echo", arguments={"msg": "safe"})
        ]),
        LLMResponse(text="done", tool_calls=[]),
    ]
    llm = ScriptedMockLLM(responses)
    tm = ToolManager()
    tm.register(ToolDef("echo", "echo", {}, ToolPermission.DANGEROUS,
                        lambda a: "ok"))
    governance = Governance()

    with tempfile.TemporaryDirectory() as td:
        loop = AgentLoop(
            llm, tm, governance,
            FeedbackPipeline([SyntaxSensor()], FailureClassifier(), CorrectionEngine()),
            ActionParser(), SessionManager(td),
            MemoryManager(InMemoryVectorStore()), Config(max_steps=10),
        )
        result = loop.run("task")
        assert result.success is True
