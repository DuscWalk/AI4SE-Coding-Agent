# coding_agent/presentation/app.py
"""FastAPI application factory for the Coding Agent Harness."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from coding_agent.presentation.routes import create_router, set_agent_loop
from coding_agent.presentation.websocket import websocket_endpoint

if TYPE_CHECKING:
    from coding_agent.application.agent_loop import AgentLoop


def create_app(loop: AgentLoop | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        loop: Optional AgentLoop instance for the /api/run endpoint.
              When None, /api/run will still create sessions but won't
              execute the agent loop.

    Returns:
        A fully configured FastAPI app with CORS, REST routes,
        WebSocket endpoint, and static file serving.
    """
    if loop is not None:
        set_agent_loop(loop)

    app = FastAPI(title="Coding Agent Harness")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(create_router())
    app.add_api_websocket_route("/ws/{session_id}", websocket_endpoint)

    @app.get("/")
    async def root():
        return RedirectResponse(url="/static/index.html")

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app