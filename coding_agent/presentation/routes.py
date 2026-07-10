# coding_agent/presentation/routes.py
"""REST API routes for the Coding Agent Harness."""
from __future__ import annotations

from fastapi import APIRouter
from coding_agent.infrastructure.credential_store import CredentialStore

store = CredentialStore()
sessions_data: list[dict] = []


def create_router() -> APIRouter:
    """Create and return the configured API router."""
    router = APIRouter(prefix="/api")

    @router.get("/status")
    async def status():
        return {"status": "running", "sessions_count": len(sessions_data)}

    @router.get("/sessions")
    async def list_sessions():
        return sessions_data

    @router.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        for s in sessions_data:
            if s.get("id") == session_id:
                return s
        return {"error": "not found"}

    @router.post("/sessions/{session_id}/cancel")
    async def cancel_session(session_id: str):
        for s in sessions_data:
            if s.get("id") == session_id:
                s["status"] = "CANCELLED"
                return {"status": "ok", "session_id": session_id}
        return {"error": "not found"}

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