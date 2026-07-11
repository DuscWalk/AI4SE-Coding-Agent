# coding_agent/presentation/websocket.py
"""WebSocket endpoint for streaming agent step updates."""
from __future__ import annotations

import asyncio
from typing import Any
from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections per session.

    AgentLoop calls broadcast() from its thread; messages are sent
    to the event loop via run_coroutine_threadsafe.
    """

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(session_id, []).append(websocket)
        await websocket.send_json({"type": "connected", "session_id": session_id})

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(session_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(session_id, None)

    def broadcast(self, session_id: str, data: dict[str, Any]) -> None:
        """Thread-safe broadcast to all connections for a session."""
        conns = list(self._connections.get(session_id, []))
        if not conns or self._loop is None:
            return
        for ws in conns:
            try:
                asyncio.run_coroutine_threadsafe(
                    ws.send_json(data), self._loop
                )
            except Exception:
                pass

    async def _handle_connection(self, websocket: WebSocket, session_id: str) -> None:
        try:
            while True:
                # Keep connection alive, receive pings
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                    # Client can send pings; we echo back for keepalive
                    await websocket.send_json({"type": "pong", "data": data})
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    try:
                        await websocket.send_json({"type": "ping"})
                    except Exception:
                        break
        except Exception:
            pass
        finally:
            self.disconnect(session_id, websocket)


# Singleton instance
ws_manager = WebSocketManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Accept WebSocket connections and stream agent step updates.

    The client connects with a session_id path parameter.
    AgentLoop step updates are broadcast to all connections for that session.
    """
    session_id = websocket.path_params.get("session_id", "unknown")
    await ws_manager.connect(session_id, websocket)
    await ws_manager._handle_connection(websocket, session_id)
