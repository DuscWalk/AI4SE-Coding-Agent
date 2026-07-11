# coding_agent/presentation/routes.py
"""REST API routes for the Coding Agent Harness."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from fastapi import APIRouter
from coding_agent.domain.models import Action
from coding_agent.infrastructure.credential_store import CredentialStatus, CredentialStore
from coding_agent.application.session_manager import SessionManager
from coding_agent.presentation.websocket import ws_manager

if TYPE_CHECKING:
    from coding_agent.application.agent_loop import AgentLoop

store = CredentialStore()
session_manager = SessionManager()
_agent_loop: AgentLoop | None = None


def set_agent_loop(loop: AgentLoop) -> None:
    """Inject an AgentLoop instance for use by the /api/run endpoint."""
    global _agent_loop, session_manager
    _agent_loop = loop
    session_manager = loop.session_manager
    # Register step callback for WebSocket broadcasting
    loop.on_step(_on_agent_step)


def _on_agent_step(
    session_id: str,
    step_number: int,
    action: Action | None,
    result: object | None,
    status: str,
) -> None:
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
    async def status() -> dict[str, Any]:
        return {"status": "running", "sessions_count": len(session_manager.list_all())}

    @router.get("/sessions")
    async def list_sessions() -> list[dict[str, Any]]:
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
    async def get_session(session_id: str) -> dict[str, Any]:
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
    async def cancel_session(session_id: str) -> dict[str, Any]:
        s = session_manager.get(session_id)
        if s is None:
            return {"error": "not found"}
        session_manager.cancel(session_id)
        return {"status": "ok", "session_id": session_id}

    @router.post("/sessions/{session_id}/approve")
    async def approve_session(
        session_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
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
    async def run_task(data: dict[str, Any]) -> dict[str, Any]:
        goal = data.get("goal", "")
        if not goal:
            return {"error": "goal is required"}
        session = session_manager.create(goal)
        # Run agent loop in background if available
        if _agent_loop is not None:
            loop_ref = _agent_loop
            asyncio.get_running_loop().run_in_executor(
                None,
                loop_ref.run,
                goal,
                session.id,
            )
        return {"session_id": session.id, "id": session.id, "status": session.status.value}

    @router.get("/credentials/status")
    async def credentials_status() -> CredentialStatus:
        return store.get_status()

    @router.post("/credentials")
    async def set_credentials(data: dict[str, Any]) -> dict[str, Any]:
        store.set_api_key(data.get("api_key", ""))
        return {"status": "ok"}

    @router.delete("/credentials")
    async def clear_credentials() -> dict[str, Any]:
        store.clear_api_key()
        return {"status": "ok"}

    return router
