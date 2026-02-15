"""
WebSocket manager for real-time frontend updates.
"""
from typing import List, Dict
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_data: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_data[websocket] = {"client_id": client_id, "subscribed": set()}
        logger.info(f"WebSocket connected: {client_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            if websocket in self.client_data:
                del self.client_data[websocket]
            logger.info("WebSocket disconnected")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_data_update(self, data_type: str, data: dict):
        """Broadcast a data update to all clients."""
        message = json.dumps({
            "type": "data_update",
            "data_type": data_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        })
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

# Global connection manager instance
manager = ConnectionManager()

async def notify_data_update(data_type: str, data: dict):
    """Notify all connected clients of a data update."""
    await manager.broadcast_data_update(data_type, data)

async def notify_games_updated(games_data: dict):
    """Notify that games data has been updated."""
    await notify_data_update("games", games_data)

async def notify_players_updated(players_data: dict):
    """Notify that players data has been updated."""
    await notify_data_update("players", players_data)

async def notify_props_updated(props_data: dict):
    """Notify that player props data has been updated."""
    await notify_data_update("player_props", props_data)