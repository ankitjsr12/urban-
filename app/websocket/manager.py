import json
import logging
import asyncio
from collections import defaultdict
from fastapi import WebSocket
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.channels: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        self.channels[channel].add(websocket)
        logger.info("Client connected to channel: %s. Active clients: %d", channel, len(self.channels[channel]))

    def disconnect(self, websocket: WebSocket, channel: str):
        self.channels[channel].discard(websocket)
        logger.info("Client disconnected from channel: %s. Active clients: %d", channel, len(self.channels[channel]))

    async def broadcast(self, channel: str, event: dict):
        """Broadcasts payload to all clients connected to the specified channel."""
        dead = []
        payload_str = json.dumps(event, default=str)
        for ws in list(self.channels[channel]):
            try:
                await ws.send_text(payload_str)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, channel)


manager = ConnectionManager()
