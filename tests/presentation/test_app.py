# tests/presentation/test_app.py
"""Tests for FastAPI presentation layer."""
from __future__ import annotations

import pytest
import time
from fastapi.testclient import TestClient
from coding_agent.presentation.app import create_app
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.models import AgentResult


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_status_endpoint(client):
    """GET /api/status should return 200 with status key."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_sessions_list(client):
    """GET /api/sessions should return 200 with a list."""
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_credentials_status(client):
    """GET /api/credentials/status should return 200 with configured key."""
    response = client.get("/api/credentials/status")
    assert response.status_code == 200
    assert "configured" in response.json()


def test_run_endpoint_creates_session(client):
    """POST /api/run should create a session and return a session_id."""
    response = client.post("/api/run", json={"goal": "Test task"})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "id" in data
    assert data["session_id"] == data["id"]


def test_run_endpoint_rejects_empty_goal(client):
    """POST /api/run with empty goal should return an error."""
    response = client.post("/api/run", json={"goal": ""})
    assert response.status_code == 200
    data = response.json()
    assert "error" in data


def test_run_endpoint_creates_visible_session(client):
    """POST /api/run creates a session that appears in GET /api/sessions."""
    response = client.post("/api/run", json={"goal": "Visible task"})
    session_id = response.json()["session_id"]

    # List sessions should include the new one
    response = client.get("/api/sessions")
    sessions = response.json()
    found = any(s["id"] == session_id for s in sessions)
    assert found, f"Session {session_id} not found in sessions list"


def test_get_session_by_id(client):
    """GET /api/sessions/{id} should return session details."""
    response = client.post("/api/run", json={"goal": "Detail test"})
    session_id = response.json()["session_id"]

    response = client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["goal"] == "Detail test"
    assert data["id"] == session_id


def test_cancel_session(client):
    """POST /api/sessions/{id}/cancel should cancel a session."""
    response = client.post("/api/run", json={"goal": "Cancel test"})
    session_id = response.json()["session_id"]

    response = client.post(f"/api/sessions/{session_id}/cancel")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

    # Verify session is cancelled
    response = client.get(f"/api/sessions/{session_id}")
    assert response.json()["status"] == "CANCELLED"


def test_approve_session(client):
    """POST /api/sessions/{id}/approve should accept approval decision."""
    response = client.post("/api/run", json={"goal": "Approve test"})
    session_id = response.json()["session_id"]

    response = client.post(
        f"/api/sessions/{session_id}/approve",
        json={"approved": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["approved"] is True


def test_approve_session_deny(client):
    """POST /api/sessions/{id}/approve with approved=false should work."""
    response = client.post("/api/run", json={"goal": "Deny test"})
    session_id = response.json()["session_id"]

    response = client.post(
        f"/api/sessions/{session_id}/approve",
        json={"approved": False},
    )
    assert response.status_code == 200
    assert response.json()["approved"] is False


def test_approve_nonexistent_session(client):
    """POST /api/sessions/{id}/approve on nonexistent session returns error."""
    response = client.post(
        "/api/sessions/nonexistent-id/approve",
        json={"approved": True},
    )
    assert response.status_code == 200
    assert "error" in response.json()


def test_run_endpoint_uses_agent_loop_session_manager(tmp_path) -> None:
    class FakeLoop:
        def __init__(self) -> None:
            self.session_manager = SessionManager(str(tmp_path / "sessions"))
            self.calls: list[tuple[str, str | None]] = []

        def on_step(self, _callback) -> None:
            return None

        def run(self, goal: str, session_id: str | None = None) -> AgentResult:
            self.calls.append((goal, session_id))
            result = AgentResult(success=True, answer="done")
            assert session_id is not None
            self.session_manager.complete(session_id, result)
            return result

        def approve_session(self, _session_id: str) -> None:
            return None

        def deny_session(self, _session_id: str) -> None:
            return None

    loop = FakeLoop()
    with TestClient(create_app(loop=loop)) as app_client:
        response = app_client.post("/api/run", json={"goal": "integrated task"})
        session_id = response.json()["session_id"]
        for _ in range(50):
            if loop.calls:
                break
            time.sleep(0.01)

    assert loop.calls == [("integrated task", session_id)]
    assert loop.session_manager.get(session_id) is not None
