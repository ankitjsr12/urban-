import json
from collections import defaultdict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.channels: dict[str, set[WebSocket]] = defaultdict(set)
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept(); self.channels[channel].add(websocket)
    def disconnect(self, websocket: WebSocket, channel: str): self.channels[channel].discard(websocket)
    async def broadcast(self, channel: str, event: dict):
        dead=[]
        for ws in self.channels[channel]:
            try: await ws.send_text(json.dumps(event, default=str))
            except Exception: dead.append(ws)
        for ws in dead: self.disconnect(ws, channel)
manager=ConnectionManager()
