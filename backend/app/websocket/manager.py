"""FLOOD-X WebSocket Connection Manager.

Manages all active WebSocket connections and broadcasts
real-time simulation state updates to all connected clients.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

import structlog
from fastapi import WebSocket, WebSocketDisconnect

log = structlog.get_logger(__name__)


class ConnectionManager:
    """Thread-safe WebSocket connection pool with broadcast support."""

    def __init__(self) -> None:
        self._active: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._active.add(websocket)
        log.info("ws_client_connected", total=len(self._active))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._active.discard(websocket)
        log.info("ws_client_disconnected", total=len(self._active))

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients. Dead connections are pruned."""
        if not self._active:
            return

        payload = json.dumps(message, default=str)
        dead: List[WebSocket] = []

        async with self._lock:
            connections = list(self._active)

        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._active.discard(ws)
            log.info("ws_pruned_dead_connections", count=len(dead))

    async def handle_connection(self, websocket: WebSocket) -> None:
        """Full lifecycle handler — accept, listen, disconnect."""
        await self.connect(websocket)

        # Send initial connection acknowledgement
        await websocket.send_text(json.dumps({
            "type": "connection_ack",
            "message": "Connected to FLOOD-X real-time stream",
            "data_mode": "SYNTHETIC_SIMULATION",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))

        try:
            while True:
                # Listen for client commands (start/pause/reset/scenario)
                data = await websocket.receive_text()
                try:
                    cmd = json.loads(data)
                    await self._handle_command(websocket, cmd)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON command",
                    }))
        except WebSocketDisconnect:
            await self.disconnect(websocket)

    async def _handle_command(
        self, websocket: WebSocket, cmd: Dict[str, Any]
    ) -> None:
        """Route client commands to the simulation engine."""
        from app.simulation.engine import SimulationEngine
        engine = SimulationEngine.get_instance()

        cmd_type = cmd.get("type", "")
        log.info("ws_command_received", cmd_type=cmd_type)

        if cmd_type == "start":
            scenario = cmd.get("scenario", "normal_rainfall")
            speed = cmd.get("speed", 1.0)
            await engine.start(scenario=scenario, speed=speed)
        elif cmd_type == "pause":
            await engine.pause()
        elif cmd_type == "resume":
            await engine.resume()
        elif cmd_type == "reset":
            await engine.reset()
        elif cmd_type == "set_rainfall":
            intensity = float(cmd.get("intensity", 20.0))
            await engine.set_rainfall_intensity(intensity)
        elif cmd_type == "ping":
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }))
        else:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Unknown command: {cmd_type}",
            }))

    @property
    def connection_count(self) -> int:
        return len(self._active)


# Singleton instance
ws_manager = ConnectionManager()
