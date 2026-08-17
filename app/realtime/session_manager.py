"""Realtime session synchronization with WebSocket transport support."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.realtime.events import RealtimeEvent, RealtimeEventType
from app.realtime.payloads import (
    AssistantStatus,
    ChatMessagePayload,
    ClientInboundMessage,
    DeviceType,
    SessionSnapshotPayload,
    WsEnvelope,
)
from app.realtime.session_state import (
    ConnectedDevice,
    RealtimeSessionData,
    default_demo_session,
    new_session,
    utc_now,
)

RealtimeSubscriber = Callable[[RealtimeEvent], None]

SESSION_ID_MAX_LEN = 128
DEVICE_ID_MAX_LEN = 128
DEVICE_NAME_MAX_LEN = 120


def _validate_session_id(session_id: str) -> None:
    if not session_id or len(session_id) > SESSION_ID_MAX_LEN:
        raise ValueError("invalid session_id")
    if not all(ch.isalnum() or ch in "-_" for ch in session_id):
        raise ValueError("invalid session_id characters")


def _validate_device_id(device_id: str) -> None:
    if not device_id or len(device_id) > DEVICE_ID_MAX_LEN:
        raise ValueError("invalid device_id")
    if not all(ch.isalnum() or ch in "-_" for ch in device_id):
        raise ValueError("invalid device_id characters")


def _validate_device_type(device_type: str) -> DeviceType:
    normalized = device_type.strip().lower()
    if normalized not in {"pc", "phone", "tablet"}:
        raise ValueError("invalid device_type")
    return normalized  # type: ignore[return-value]


class RealtimeSessionManager:
    """
    Manages in-memory repair sessions, device presence, and event fan-out.

    Authentication and authorization will be implemented before production deployment.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[RealtimeSubscriber]] = defaultdict(list)
        self._event_log: list[RealtimeEvent] = []
        self._sessions: dict[str, RealtimeSessionData] = {}
        self._ws_connections: dict[str, dict[str, Any]] = {}

    # --- Session lifecycle ---

    def create_session(
        self,
        session_id: str | None = None,
        *,
        seed_demo: bool = False,
    ) -> RealtimeSessionData:
        if session_id:
            _validate_session_id(session_id)
            if session_id in self._sessions:
                return self._sessions[session_id]
            data = default_demo_session(session_id) if seed_demo else new_session(session_id)
        else:
            data = default_demo_session(str(uuid4())) if seed_demo else new_session()
        self._sessions[data.session_id] = data
        self.emit(
            data.session_id,
            RealtimeEventType.SESSION_CREATED,
            payload=data.snapshot().model_dump(mode="json"),
        )
        return data

    def get_session(self, session_id: str) -> RealtimeSessionData | None:
        return self._sessions.get(session_id)

    def get_or_create_session(
        self,
        session_id: str,
        *,
        seed_demo: bool = False,
    ) -> RealtimeSessionData:
        existing = self.get_session(session_id)
        if existing:
            return existing
        return self.create_session(session_id, seed_demo=seed_demo)

    # --- Pub/sub (in-process) ---

    def subscribe(self, repair_session_id: str, handler: RealtimeSubscriber) -> None:
        self._subscribers[repair_session_id].append(handler)

    def unsubscribe(self, repair_session_id: str, handler: RealtimeSubscriber) -> None:
        handlers = self._subscribers.get(repair_session_id, [])
        self._subscribers[repair_session_id] = [h for h in handlers if h != handler]

    def emit(
        self,
        repair_session_id: str,
        event_type: RealtimeEventType,
        payload: dict[str, Any] | None = None,
        source_client_device_id: str | None = None,
    ) -> RealtimeEvent:
        event = RealtimeEvent(
            id=str(uuid4()),
            repair_session_id=repair_session_id,
            event_type=event_type,
            payload=payload or {},
            emitted_at=datetime.now(timezone.utc),
            source_client_device_id=source_client_device_id,
        )
        self._event_log.append(event)
        for handler in self._subscribers.get(repair_session_id, []):
            handler(event)
        return event

    def events_for_session(self, repair_session_id: str) -> list[RealtimeEvent]:
        return [
            event
            for event in self._event_log
            if event.repair_session_id == repair_session_id
        ]

    # --- WebSocket connections ---

    def register_ws(
        self,
        session_id: str,
        device_id: str,
        send_json: Callable[[dict[str, Any]], Any],
    ) -> None:
        key = f"{session_id}:{device_id}"
        self._ws_connections[key] = {
            "session_id": session_id,
            "device_id": device_id,
            "send_json": send_json,
        }

    def unregister_ws(self, session_id: str, device_id: str) -> None:
        key = f"{session_id}:{device_id}"
        self._ws_connections.pop(key, None)

    async def _send_ws(self, session_id: str, device_id: str, envelope: WsEnvelope) -> None:
        key = f"{session_id}:{device_id}"
        conn = self._ws_connections.get(key)
        if not conn:
            return
        payload = envelope.model_dump(mode="json")
        result = conn["send_json"](payload)
        if asyncio.iscoroutine(result):
            await result

    async def broadcast_ws(
        self,
        session_id: str,
        envelope: WsEnvelope,
        *,
        exclude_device_id: str | None = None,
    ) -> None:
        tasks = []
        for key, conn in self._ws_connections.items():
            if conn["session_id"] != session_id:
                continue
            if exclude_device_id and conn["device_id"] == exclude_device_id:
                continue
            tasks.append(self._send_ws(session_id, conn["device_id"], envelope))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_event_ws(
        self,
        session_id: str,
        event: RealtimeEvent,
        *,
        exclude_device_id: str | None = None,
    ) -> None:
        await self.broadcast_ws(
            session_id,
            WsEnvelope(type="event", event=event.model_dump(mode="json")),
            exclude_device_id=exclude_device_id,
        )

    # --- Device presence ---

    async def connect_device(
        self,
        session_id: str,
        device_id: str,
        device_type: str,
        device_name: str,
        *,
        seed_demo: bool = False,
    ) -> tuple[RealtimeSessionData, SessionSnapshotPayload]:
        _validate_session_id(session_id)
        _validate_device_id(device_id)
        dtype = _validate_device_type(device_type)
        name = (device_name or device_id)[:DEVICE_NAME_MAX_LEN]
        session = self.get_or_create_session(session_id, seed_demo=seed_demo)
        now = utc_now()
        session.devices[device_id] = ConnectedDevice(
            device_id=device_id,
            device_type=dtype,
            device_name=name,
            connected_at=now,
            last_seen=now,
            online=True,
        )
        payload = session.devices[device_id]
        event = self.emit(
            session_id,
            RealtimeEventType.DEVICE_CONNECTED,
            payload={
                "device_id": payload.device_id,
                "device_type": payload.device_type,
                "device_name": payload.device_name,
                "online": True,
                "connected_at": payload.connected_at.isoformat(),
                "last_seen": payload.last_seen.isoformat(),
            },
            source_client_device_id=device_id,
        )
        await self.send_event_ws(session_id, event, exclude_device_id=device_id)
        snapshot = session.snapshot()
        return session, snapshot

    async def disconnect_device(self, session_id: str, device_id: str) -> None:
        session = self.get_session(session_id)
        if not session:
            return
        device = session.devices.get(device_id)
        if device:
            device.online = False
            device.last_seen = utc_now()
            event = self.emit(
                session_id,
                RealtimeEventType.DEVICE_DISCONNECTED,
                payload={
                    "device_id": device.device_id,
                    "device_type": device.device_type,
                    "device_name": device.device_name,
                    "online": False,
                    "last_seen": device.last_seen.isoformat(),
                },
                source_client_device_id=device_id,
            )
            await self.send_event_ws(session_id, event)
        self.unregister_ws(session_id, device_id)

    async def heartbeat(self, session_id: str, device_id: str) -> None:
        session = self.get_session(session_id)
        if not session:
            return
        device = session.devices.get(device_id)
        if not device:
            return
        device.last_seen = utc_now()
        device.online = True
        event = self.emit(
            session_id,
            RealtimeEventType.DEVICE_HEARTBEAT,
            payload={
                "device_id": device.device_id,
                "last_seen": device.last_seen.isoformat(),
                "online": True,
            },
            source_client_device_id=device_id,
        )
        await self.send_event_ws(session_id, event, exclude_device_id=device_id)

    # --- Chat & status ---

    async def add_chat_message(
        self,
        session_id: str,
        device_id: str,
        content: str,
        role: str = "user",
    ) -> ChatMessagePayload:
        session = self.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        message = ChatMessagePayload(
            message_id=str(uuid4()),
            session_id=session_id,
            device_id=device_id if role == "user" else None,
            role=role,  # type: ignore[arg-type]
            content=content.strip(),
            timestamp=utc_now().strftime("%H:%M"),
        )
        session.messages.append(message)
        payload = message.model_dump(mode="json")
        event = self.emit(
            session_id,
            RealtimeEventType.CHAT_MESSAGE,
            payload=payload,
            source_client_device_id=device_id,
        )
        await self.send_event_ws(session_id, event)
        return message

    async def set_assistant_status(
        self,
        session_id: str,
        status: AssistantStatus,
        *,
        source_device_id: str | None = None,
    ) -> None:
        session = self.get_session(session_id)
        if not session:
            return
        session.assistant_status = status
        event = self.emit(
            session_id,
            RealtimeEventType.ASSISTANT_STATUS,
            payload={"status": status},
            source_client_device_id=source_device_id,
        )
        await self.send_event_ws(session_id, event)

    async def handle_client_message(
        self,
        session_id: str,
        device_id: str,
        raw: dict[str, Any],
    ) -> None:
        message = ClientInboundMessage.model_validate(raw)
        if message.type == "heartbeat":
            await self.heartbeat(session_id, device_id)
            return
        if message.type == "assistant_status" and message.status:
            await self.set_assistant_status(
                session_id,
                message.status,
                source_device_id=device_id,
            )
            return
        if message.type == "chat_message":
            if not message.content:
                raise ValueError("content required")
            await self.add_chat_message(
                session_id,
                device_id,
                message.content,
                role=message.role,
            )
            return
        raise ValueError("unsupported message type")

    def connection_count(self, session_id: str | None = None) -> int:
        if session_id is None:
            return len(self._ws_connections)
        return sum(1 for c in self._ws_connections.values() if c["session_id"] == session_id)


# Singleton for app lifespan
realtime_manager = RealtimeSessionManager()
