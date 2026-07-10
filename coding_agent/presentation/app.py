# coding_agent/presentation/app.py
"""FastAPI application factory for the Coding Agent Harness."""
from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from coding_agent.presentation.routes import create_router
from coding_agent.presentation.websocket import websocket_endpoint


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully configured FastAPI app with CORS, REST routes,
        WebSocket endpoint, and static file serving.
    """
    app = FastAPI(title="Coding Agent Harness")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(create_router())
    app.add_api_websocket_route("/ws/{session_id}", websocket_endpoint)

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app