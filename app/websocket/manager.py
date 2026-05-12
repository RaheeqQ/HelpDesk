from fastapi import WebSocket
from collections import defaultdict


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict[str, WebSocket]] = defaultdict(dict)

    async def connect(
        self,
        conversation_id: str,
        user_id: str,
        websocket: WebSocket
    ):
        await websocket.accept()

        self.active_connections[conversation_id][user_id] = websocket

    def disconnect(
        self,
        conversation_id: str,
        user_id: str
    ):
        if user_id in self.active_connections.get(conversation_id, {}):
            del self.active_connections[conversation_id][user_id]

        if not self.active_connections[conversation_id]:
            del self.active_connections[conversation_id]

    async def broadcast_message(
        self,
        conversation_id: str,
        message: str
    ):
        connections = self.active_connections.get(conversation_id, {})

        disconnected_users = []

        for user_id, connection in connections.items():
            try:
                await connection.send_json(message)

            except Exception:
                disconnected_users.append(user_id)

        for user_id in disconnected_users:
            self.disconnect(conversation_id, user_id)


manager = ConnectionManager()