from __future__ import annotations

import time
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """管理所有 WebSocket 客户端连接，并支持向全体广播。"""

    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def send(self, ws: WebSocket, msg: dict[str, Any]) -> None:
        try:
            await ws.send_json(msg)
        except Exception:
            self.disconnect(ws)

    async def broadcast(self, type: str, data: Any = None) -> None:
        msg: dict[str, Any] = {"type": type, "timestamp": int(time.time() * 1000)}
        if data is not None:
            msg["data"] = data
        for ws in list(self.active):
            await self.send(ws, msg)


manager = ConnectionManager()
