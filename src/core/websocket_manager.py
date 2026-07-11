from fastapi import WebSocket
from typing import Set, Callable, Dict, Any
import logging
import json

class WebsocketManager:
    """
    Manages active WebSocket connections, handles message dispatch, 
    and facilitates real-time telemetry broadcasting.
    """
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._message_handlers: Set[Callable[[Dict[str, Any]], None]] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    def register_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Register callback for incoming messages."""
        self._message_handlers.add(handler)

    def unregister_handler(self, handler: Callable[[Dict[str, Any]], None]):
        self._message_handlers.discard(handler)

    async def handle_incoming(self, websocket: WebSocket):
        """Infinite loop to receive messages from a specific socket."""
        try:
            while True:
                text_data = await websocket.receive_text()
                try:
                    data = json.loads(text_data)
                    if isinstance(data, dict):
                        for handler in self._message_handlers:
                            handler(data)
                except Exception as e:
                    pass # Ignore malformed json
        except Exception:
            pass
        finally:
            self.disconnect(websocket)

    async def broadcast(self, payload: Dict[str, Any]):
        """Broadcast JSON payload to all active websockets."""
        if not self.active_connections:
            return
            
        dead_connections = set()
        for ws in list(self.active_connections):
            try:
                await ws.send_json(payload)
            except Exception:
                dead_connections.add(ws)
                
        self.active_connections.difference_update(dead_connections)
