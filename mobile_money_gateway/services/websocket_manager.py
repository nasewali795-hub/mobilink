from typing import Dict, Set, Optional
from fastapi import WebSocket
import json
import asyncio
from mobile_money_gateway.config import settings


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.gateway_connections: Dict[str, WebSocket] = {}

    async def connect_tablet(self, websocket: WebSocket, booth_id: str):
        await websocket.accept()
        self.active_connections[booth_id] = websocket

    async def connect_gateway(self, websocket: WebSocket, gateway_id: str):
        await websocket.accept()
        self.gateway_connections[gateway_id] = websocket

    def disconnect_tablet(self, booth_id: str):
        if booth_id in self.active_connections:
            del self.active_connections[booth_id]

    def disconnect_gateway(self, gateway_id: str):
        if gateway_id in self.gateway_connections:
            del self.gateway_connections[gateway_id]

    async def send_to_tablet(self, booth_id: str, message: dict):
        if booth_id in self.active_connections:
            try:
                await self.active_connections[booth_id].send_json(message)
            except Exception:
                self.disconnect_tablet(booth_id)

    async def send_to_gateway(self, gateway_id: str, message: dict):
        if gateway_id in self.gateway_connections:
            try:
                await self.gateway_connections[gateway_id].send_json(message)
            except Exception:
                self.disconnect_gateway(gateway_id)

    async def broadcast_to_tablets(self, message: dict):
        disconnected = []
        for booth_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(booth_id)
        for booth_id in disconnected:
            self.disconnect_tablet(booth_id)

    def get_connected_booths(self) -> Set[str]:
        return set(self.active_connections.keys())

    def get_connected_gateways(self) -> Set[str]:
        return set(self.gateway_connections.keys())


manager = ConnectionManager()
