# coding_agent/presentation/websocket.py
"""WebSocket endpoint for streaming agent step updates."""
from __future__ import annotations

from fastapi import WebSocket


async def websocket_endpoint(websocket: WebSocket):
    """Accept WebSocket connections and echo received messages.

    In a full implementation, this would stream agent step updates
    to connected clients. Currently provides a basic echo service
    to validate the WebSocket transport.
    """
    await websocket.accept()
    await websocket.send_json({"type": "connected"})
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "echo", "data": data})
    except Exception:
        pass