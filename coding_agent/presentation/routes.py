# coding_agent/presentation/routes.py
"""REST API routes for the Coding Agent Harness."""
from __future__ import annotations

import asyncio
import uuid
from fastapi import APIRouter
from coding_agent.infrastructure.credential_store import CredentialStore
from coding_agent.application.session_manager import SessionManager
from coding_agent.presentation.websocket import ws_manager

store = CredentialStore()
session_manager = SessionManager()
_agent_loop = None


def set_agent_loop(loop):
    """Inject an AgentLoop instance for use by the /api/run endpoint."""
    global _agent_loop
    _agent_loop = loop
    # Register step callback for WebSocket broadcasting
    loop.on_step(_on_agent_step)


def _on_agent_step(session_id: str, step_number: int, action, result, status: str):
    """Callback from AgentLoop thread — broadcast step update via WebSocket."""
    ws_manager.broadcast(session_id, {
        "type": "step_update",
        "session_id": session_id,
        "step_number": step_number,
        "action": action.model_dump() if action else None,
        "status": status,
    })


def create_router() -> APIRouter:
    """Create and return the configured API router."""
    router = APIRouter(prefix="/api")

    @router.get("/status")
    async def status():
        return {"status": "running", "sessions_count": len(session_manager.list_all())}

    @router.get("/sessions")
    async def list_sessions():
        sessions = session_manager.list_all()
        return [
            {
                "id": s.id,
                "goal": s.goal,
                "status": s.status.value,
                "steps": len(s.steps),
            }
            for s in sessions
        ]

    @router.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        s = session_manager.get(session_id)
        if s is None:
            return {"error": "not found"}
        return {
            "id": s.id,
            "goal": s.goal,
            "status": s.status.value,
            "steps": [step.model_dump() for step in s.steps],
            "result": s.result.model_dump() if s.result else None,
        }

    @router.post("/sessions/{session_id}/cancel")
    async def cancel_session(session_id: str):
        s = session_manager.get(session_id)
        if s is None:
            return {"error": "not found"}
        session_manager.cancel(session_id)
        return {"status": "ok", "session_id": session_id}

    @router.post("/sessions/{session_id}/approve")
    async def approve_session(session_id: str, data: dict):
        s = session_manager.get(session_id)
        if s is None:
            return {"error": "not found"}
        approved = data.get("approved", False)
        if _agent_loop is not None:
            if approved:
                _agent_loop.approve_session(session_id)
            else:
                _agent_loop.deny_session(session_id)
        return {"status": "ok", "session_id": session_id, "approved": approved}

    @router.post("/run")
    async def run_task(data: dict):
        goal = data.get("goal", "")
        if not goal:
            return {"error": "goal is required"}
        session = session_manager.create(goal)
        # Run agent loop in background if available
        if _agent_loop is not None:
            loop_ref = _agent_loop
            asyncio.get_running_loop().run_in_executor(None, loop_ref.run, goal)
        return {"session_id": session.id, "id": session.id, "status": session.status.value}

    @router.get("/credentials/status")
    async def credentials_status():
        return store.get_status()

    @router.post("/credentials")
    async def set_credentials(data: dict):
        store.set_api_key(data.get("api_key", ""))
        return {"status": "ok"}

    @router.delete("/credentials")
    async def clear_credentials():
        store.clear_api_key()
        return {"status": "ok"}

    return router