from __future__ import annotations
import tempfile
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.models import SessionStatus, StepRecord, AgentResult


def test_create_session():
    with tempfile.TemporaryDirectory() as td:
        sm = SessionManager(td)
        session = sm.create("write a test function")
        assert session.goal == "write a test function"
        assert session.status == SessionStatus.RUNNING
        assert sm.get(session.id) is not None


def test_add_step_and_complete():
    with tempfile.TemporaryDirectory() as td:
        sm = SessionManager(td)
        session = sm.create("task")
        step = StepRecord(step_number=1)
        sm.add_step(session.id, step)
        sm.complete(session.id, AgentResult(success=True, answer="done"))
        assert len(session.steps) == 1
        assert session.status == SessionStatus.COMPLETED


def test_cancel_session():
    with tempfile.TemporaryDirectory() as td:
        sm = SessionManager(td)
        session = sm.create("task")
        sm.cancel(session.id)
        assert session.status == SessionStatus.CANCELLED


def test_list_all():
    with tempfile.TemporaryDirectory() as td:
        sm = SessionManager(td)
        sm.create("task 1")
        sm.create("task 2")
        assert len(sm.list_all()) == 2