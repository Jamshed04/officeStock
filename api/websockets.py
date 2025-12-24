from fastapi import WebSocket
from pydantic import BaseModel


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str | dict | BaseModel):
        if isinstance(message, (dict, BaseModel)):
            if isinstance(message, BaseModel):
                message = message.model_dump_json()
            else:
                import json
                message = json.dumps(message)

        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()