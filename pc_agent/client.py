"""PC Agent WebSocket client with registration, heartbeat, and reconnect."""

from __future__ import annotations

import asyncio
import json
import logging
from enum import Enum
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

from pc_agent.commands import configure_dispatcher, handle_command
from pc_agent.config import AgentConfig
from pc_agent.device_scanner import DeviceScanner

logger = logging.getLogger("alpilab.pc_agent")


class AgentState(str, Enum):
    OFFLINE = "OFFLINE"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    REGISTERING = "REGISTERING"
    ONLINE = "ONLINE"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


class AgentClient:
    """Async WebSocket client for Alpilab PC Agent V0.1."""

    def __init__(self, config: AgentConfig, agent_id: str) -> None:
        self.config = config
        self.agent_id = agent_id
        self.state = AgentState.OFFLINE
        self._ws: ClientConnection | None = None
        self._stop = asyncio.Event()
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._scanner: DeviceScanner | None = None
        self._reconnect_attempts = 0
        configure_dispatcher(
            {
                "safe_test": config.capabilities_safe_test,
                "windows_apps": config.capabilities_windows_apps,
                "alpilab_check": config.capabilities_alpilab_check,
                "microscope": config.capabilities_microscope,
                "thermal_camera": config.capabilities_thermal_camera,
                "multimeter": config.capabilities_multimeter,
                "power_supply": config.capabilities_power_supply,
                "iphone_panic": config.capabilities_iphone_panic,
            }
        )

    @property
    def url(self) -> str:
        return self.config.websocket_url(self.agent_id)

    async def run(self) -> None:
        while not self._stop.is_set():
            try:
                await self._connect_once()
                self._reconnect_attempts = 0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Connection error: %s", exc)
                self.state = AgentState.RECONNECTING
                delay = min(
                    self.config.reconnect_base_delay_sec * (2 ** self._reconnect_attempts),
                    self.config.reconnect_max_delay_sec,
                )
                self._reconnect_attempts += 1
                if self._reconnect_attempts > self.config.reconnect_max_attempts:
                    self.state = AgentState.ERROR
                    logger.error("Max reconnect attempts reached")
                    return
                logger.info("Reconnecting in %.0fs...", delay)
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=delay)
                    return
                except asyncio.TimeoutError:
                    continue

    async def shutdown(self) -> None:
        self._stop.set()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._ws:
            await self._ws.close()
        self.state = AgentState.OFFLINE

    async def _connect_once(self) -> None:
        self.state = AgentState.CONNECTING
        logger.info("Connecting to %s", self.url)
        async with websockets.connect(self.url) as ws:
            self._ws = ws
            self.state = AgentState.CONNECTED
            logger.info("Connected")
            await self._register(ws)
            self.state = AgentState.ONLINE
            logger.info("ONLINE")
            self._heartbeat_task = asyncio.create_task(self._heartbeat_sender(ws))
            self._scanner = DeviceScanner(on_change=self._send_detected_devices)
            self._scanner.start()
            try:
                async for raw in ws:
                    await self._handle_message(ws, raw)
            finally:
                if self._scanner:
                    self._scanner.stop()
                    self._scanner = None
                if self._heartbeat_task:
                    self._heartbeat_task.cancel()
                    self._heartbeat_task = None
                self._ws = None
                self.state = AgentState.OFFLINE

    async def _register(self, ws: ClientConnection) -> None:
        self.state = AgentState.REGISTERING
        payload = {
            "type": "register",
            "agent_id": self.agent_id,
            "agent_name": self.config.agent_name,
            "platform": self.config.platform,
            "agent_version": self.config.agent_version,
            "capabilities": {
                "safe_test": self.config.capabilities_safe_test,
                "windows_apps": self.config.capabilities_windows_apps,
                "alpilab_check": self.config.capabilities_alpilab_check,
                "microscope": self.config.capabilities_microscope,
                "thermal_camera": self.config.capabilities_thermal_camera,
                "multimeter": self.config.capabilities_multimeter,
                "power_supply": self.config.capabilities_power_supply,
                "iphone_panic": self.config.capabilities_iphone_panic,
            },
            "status": "ONLINE",
        }
        await ws.send(json.dumps(payload))
        response = json.loads(await ws.recv())
        if response.get("type") != "registered":
            raise RuntimeError(f"Registration failed: {response}")
        logger.info("Registered")

    async def _heartbeat_sender(self, ws: ClientConnection) -> None:
        while not self._stop.is_set():
            await asyncio.sleep(self.config.heartbeat_interval_sec)
            try:
                await ws.send(json.dumps({"type": "heartbeat"}))
                logger.debug("Heartbeat sent")
            except websockets.ConnectionClosed:
                break

    async def _send_detected_devices(self, devices: list[dict]) -> None:
        """Callback from DeviceScanner — sends device list to Hub."""
        if self._ws is None:
            return
        try:
            await self._ws.send(json.dumps({
                "type": "detected_devices_update",
                "devices": devices,
            }))
            logger.info("Sent detected_devices_update (%d devices)", len(devices))
        except Exception:
            logger.debug("Failed to send detected_devices_update", exc_info=True)

    async def _handle_message(self, ws: ClientConnection, raw: str | bytes) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from server")
            return

        msg_type = data.get("type")
        if msg_type == "heartbeat_ack":
            logger.debug("Heartbeat OK")
            return
        if msg_type == "command" and data.get("command"):
            await self._handle_command_message(ws, data)
            return
        if msg_type == "command_rejected":
            logger.warning("Command rejected: %s", data.get("message"))
            return
        if msg_type == "error":
            logger.warning("Server error: %s", data.get("message"))

    async def _handle_command_message(
        self,
        ws: ClientConnection,
        envelope: dict[str, Any],
    ) -> None:
        command = envelope.get("command") or {}
        cmd_type = str(command.get("type", ""))
        logger.info("Received %s", cmd_type)
        if cmd_type == "TOOL_EXECUTE":
            payload = command.get("payload") or {}
            logger.info("Received TOOL_EXECUTE tool=%s", payload.get("tool_id"))
        result = handle_command(command, self.agent_id)
        if result is None:
            logger.warning("Malformed command envelope")
            return
        if result.get("success"):
            logger.info("%s completed", cmd_type)
        else:
            logger.warning("%s rejected: %s", cmd_type, result.get("error"))
        await ws.send(json.dumps(result))
