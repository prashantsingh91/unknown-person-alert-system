"""
WebSocket Connection Manager
Handles multiple client connections and broadcasts
"""
from fastapi import WebSocket
from typing import List, Dict, Any
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and register new connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_frame(self, frame_data: bytes, detections: List[Dict]):
        """
        Broadcast video frame with detection results
        
        Args:
            frame_data: JPEG encoded frame
            detections: List of detection dictionaries
        """
        import base64
        
        message = {
            'type': 'frame',
            'frame': base64.b64encode(frame_data).decode('utf-8'),
            'detections': detections
        }
        
        await self.broadcast(message)
    
    async def broadcast_alert(self, alert_data: Dict):
        """
        Broadcast unknown person alert
        
        Args:
            alert_data: Alert information dictionary
        """
        message = {
            'type': 'alert',
            'data': alert_data
        }
        
        await self.broadcast(message)
    
    async def broadcast_metrics(self, metrics: Dict):
        """
        Broadcast system metrics
        
        Args:
            metrics: Metrics dictionary
        """
        message = {
            'type': 'metrics',
            'data': metrics
        }
        
        await self.broadcast(message)
    
    async def broadcast_known_person(self, person_data: Dict):
        """
        Broadcast known person detection
        
        Args:
            person_data: Person information dictionary
        """
        message = {
            'type': 'known_person',
            'data': person_data
        }
        
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

