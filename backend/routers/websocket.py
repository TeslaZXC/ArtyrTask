"""
WebSocket router for real-time board updates.
Endpoint: WS /ws/board/{board_id}?token=<jwt>
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Set
import json
import models
from auth import SECRET_KEY, ALGORITHM
from jose import JWTError, jwt

router = APIRouter(tags=["websocket"])

# board_id -> set of connected WebSocket clients
_connections: Dict[int, Set[WebSocket]] = {}


class ConnectionManager:
    async def connect(self, board_id: int, ws: WebSocket):
        await ws.accept()
        _connections.setdefault(board_id, set()).add(ws)

    def disconnect(self, board_id: int, ws: WebSocket):
        if board_id in _connections:
            _connections[board_id].discard(ws)
            if not _connections[board_id]:
                del _connections[board_id]

    async def broadcast(self, board_id: int, message: dict, exclude: WebSocket = None):
        dead = set()
        for ws in list(_connections.get(board_id, [])):
            if ws is exclude:
                continue
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(board_id, ws)


manager = ConnectionManager()


async def broadcast_refresh(board_id: int, entity: str = "board"):
    """Call this from other routers after any mutation."""
    await manager.broadcast(board_id, {"type": "refresh", "entity": entity, "boardId": board_id})


@router.websocket("/ws/board/{board_id}")
async def websocket_endpoint(board_id: int, ws: WebSocket, token: str = Query(...)):
    # Validate token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            await ws.close(code=4001)
            return
    except JWTError:
        await ws.close(code=4001)
        return

    await manager.connect(board_id, ws)
    try:
        while True:
            # We just keep the connection alive; clients don't send data
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(board_id, ws)
