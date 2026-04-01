from fastapi import WebSocket


class TelemetryHub:
    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = {}

    async def connect(self, device_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(device_id, set()).add(websocket)

    def disconnect(self, device_id: int, websocket: WebSocket):
        if device_id in self.connections:
            self.connections[device_id].discard(websocket)
            if not self.connections[device_id]:
                self.connections.pop(device_id, None)

    async def broadcast(self, device_id: int, payload: dict):
        sockets = self.connections.get(device_id, set()).copy()
        dead_sockets = []
        for socket in sockets:
            try:
                await socket.send_json(payload)
            except Exception:
                dead_sockets.append(socket)
        for socket in dead_sockets:
            self.disconnect(device_id, socket)
