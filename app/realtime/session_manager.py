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
    StateUpdateRejectedPayload,
    WsEnvelope,
)
from app.realtime.session_state import (
    ConnectedDevice,
    RealtimeSessionData,
    apply_demo_seed,
    default_demo_session,
    default_repair_diagnostics,
    new_session,
    session_is_unseeded,
    utc_now,
)
from app.realtime.state_sync import (
    StateUpdateRejected,
    apply_assistant_status_change,
    apply_diagnosis_pause,
    apply_diagnostic_update,
    apply_repair_context_update,
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

    def __init__(self, persistence_store: Any | None = None) -> None:
        self._subscribers: dict[str, list[RealtimeSubscriber]] = defaultdict(list)
        self._event_log: list[RealtimeEvent] = []
        self._sessions: dict[str, RealtimeSessionData] = {}
        self._ws_connections: dict[str, dict[str, Any]] = {}
        self._persistence_store = persistence_store

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
        self._persist_session(data.session_id)
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
            if seed_demo and session_is_unseeded(existing):
                apply_demo_seed(existing)
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

    async def send_snapshot_ws(self, session_id: str, device_id: str) -> None:
        session = self.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        if self._ensure_repair_diagnostics(session):
            session.state_version += 1
            self._persist_session(session_id)
        await self._send_ws(
            session_id,
            device_id,
            WsEnvelope(
                type="snapshot",
                payload=session.snapshot().model_dump(mode="json"),
            ),
        )

    async def send_state_rejected(
        self,
        session_id: str,
        device_id: str,
        exc: StateUpdateRejected,
    ) -> None:
        session = self.get_session(session_id)
        if not session:
            return
        payload = StateUpdateRejectedPayload(
            reason=str(exc.reason),
            request_type=exc.request_type,
            state_version=session.state_version,
        )
        event = self.emit(
            session_id,
            RealtimeEventType.STATE_UPDATE_REJECTED,
            payload=payload.model_dump(mode="json"),
            source_client_device_id=device_id,
        )
        await self._send_ws(
            session_id,
            device_id,
            WsEnvelope(type="event", event=event.model_dump(mode="json")),
        )

    def _apply_repair_context_fields(
        self,
        session: RealtimeSessionData,
        ctx: dict[str, Any],
    ) -> None:
        if "label" in ctx and ctx["label"] is not None:
            session.label = str(ctx["label"])
        if "device" in ctx:
            session.device = ctx["device"]
        if "issue" in ctx:
            session.issue = ctx["issue"]
        if "status" in ctx and ctx["status"] is not None:
            session.status = str(ctx["status"])
        if "diagnosis_label" in ctx and ctx["diagnosis_label"] is not None:
            session.diagnosis_label = str(ctx["diagnosis_label"])

    async def _broadcast_state_update(
        self,
        session_id: str,
        device_id: str,
        changes: dict[str, Any],
    ) -> RealtimeEvent:
        session = self.get_session(session_id)
        if not session:
            raise ValueError("session not found")

        if "repair_context" in changes:
            self._apply_repair_context_fields(session, changes["repair_context"])

        if "assistant_status" in changes:
            session.assistant_status = changes["assistant_status"]

        session.state_version += 1
        payload = {
            "event_id": str(uuid4()),
            "session_id": session_id,
            "timestamp": utc_now().isoformat(),
            "source_device_id": device_id,
            "state_version": session.state_version,
            "changes": changes,
        }
        event = self.emit(
            session_id,
            RealtimeEventType.SESSION_STATE_UPDATED,
            payload=payload,
            source_client_device_id=device_id,
        )
        await self.send_event_ws(session_id, event)
        self._persist_session(session_id)
        return event

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
        if self._ensure_repair_diagnostics(session):
            session.state_version += 1
        snapshot = session.snapshot()
        self._persist_session(session_id)
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

    def _seed_diagnostics_if_empty(self, session: RealtimeSessionData) -> bool:
        if session.diagnostics:
            return False
        session.diagnostics = default_repair_diagnostics()
        if not session.diagnosis_label:
            session.diagnosis_label = "Diagnosis in progress"
        return True

    def _session_has_repair_activity(self, session: RealtimeSessionData) -> bool:
        return bool(session.messages or session.device_context or session.device)

    def _ensure_repair_diagnostics(self, session: RealtimeSessionData) -> bool:
        """Seed standard tests when a repair is active but diagnostics were cleared."""
        if session.diagnostics or not self._session_has_repair_activity(session):
            return False
        return self._seed_diagnostics_if_empty(session)

    async def _broadcast_diagnostics_seed(
        self,
        session_id: str,
        device_id: str,
        session: RealtimeSessionData,
    ) -> None:
        await self._broadcast_state_update(
            session_id,
            device_id,
            {
                "diagnostics": [t.model_dump(mode="json") for t in session.diagnostics],
                "repair_context": {"diagnosis_label": session.diagnosis_label},
            },
        )

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
        seeded = role == "user" and self._seed_diagnostics_if_empty(session)
        session.messages.append(message)
        session.state_version += 1
        payload = message.model_dump(mode="json")
        event = self.emit(
            session_id,
            RealtimeEventType.CHAT_MESSAGE,
            payload=payload,
            source_client_device_id=device_id,
        )
        await self.send_event_ws(session_id, event)
        if seeded:
            await self._broadcast_diagnostics_seed(session_id, device_id, session)
        self._persist_session(session_id)
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
        changes = apply_assistant_status_change(status)
        await self._broadcast_state_update(
            session_id,
            source_device_id or "system",
            changes,
        )
        event = self.emit(
            session_id,
            RealtimeEventType.ASSISTANT_STATUS,
            payload={"status": status, "state_version": session.state_version},
            source_client_device_id=source_device_id,
        )
        await self.send_event_ws(session_id, event)

    async def update_diagnostic_measurement(
        self,
        session_id: str,
        device_id: str,
        test_id: str,
        value: str,
    ) -> None:
        session = self.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        if session.status == "paused":
            raise StateUpdateRejected(
                "diagnosis is paused",
                request_type="diagnostic_update",
            )
        _, changes = apply_diagnostic_update(session.diagnostics, test_id, value)
        await self._broadcast_state_update(session_id, device_id, changes)
        event = self.emit(
            session_id,
            RealtimeEventType.DIAGNOSTIC_UPDATED,
            payload={
                "tests": [t.model_dump(mode="json") for t in session.diagnostics],
                "state_version": session.state_version,
            },
            source_client_device_id=device_id,
        )
        await self.send_event_ws(session_id, event)

    async def set_diagnosis_paused(
        self,
        session_id: str,
        device_id: str,
        paused: bool,
    ) -> None:
        session = self.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        changes = apply_diagnosis_pause(paused)
        await self._broadcast_state_update(session_id, device_id, changes)

    async def update_repair_context(
        self,
        session_id: str,
        device_id: str,
        *,
        device: str | None = None,
        issue: str | None = None,
        label: str | None = None,
    ) -> None:
        session = self.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        changes = apply_repair_context_update(device=device, issue=issue, label=label)
        await self._broadcast_state_update(session_id, device_id, changes)

    async def update_detected_devices(
        self,
        session_id: str,
        devices: list[dict[str, Any]],
    ) -> None:
        """Replace the detected-device list (called by PC Agent scanner)."""
        from app.schemas.device_context import DetectedDevice

        session = self.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        session.detected_devices = [DetectedDevice.model_validate(d) for d in devices]
        session.state_version += 1
        event = self.emit(
            session_id,
            RealtimeEventType.REPAIR_DEVICE_LIST_UPDATED,
            payload={"detected_devices": [d.model_dump(mode="json") for d in session.detected_devices]},
        )
        await self.send_event_ws(session_id, event)
        self._persist_session(session_id)

    def _ensure_diagnostic_card(
        self,
        session_id: str,
        device_id: str,
        device_name: str,
    ) -> None:
        """Create a diagnostic card when a device is associated (idempotent)."""
        from app.models.database import SessionLocal
        from app.services.diagnostic_card_service import DiagnosticCardService

        db = SessionLocal()
        try:
            DiagnosticCardService(db).get_or_create_card(
                session_id=session_id,
                device_id=device_id,
                device_name=device_name,
            )
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Failed to ensure diagnostic card session=%s device=%s",
                session_id,
                device_id,
            )
        finally:
            db.close()

    def clear_session_workspace(self, session_id: str) -> None:
        """Reset in-memory repair UI state while keeping the same session id."""
        session = self.get_or_create_session(session_id, seed_demo=False)
        session.messages.clear()
        session.diagnostics.clear()
        session.device = None
        session.issue = None
        session.device_context = None
        session.detected_devices.clear()
        session.product_search_context = None
        session.label = "Repair Session"
        session.diagnosis_label = ""
        session.status = "active"
        session.state_version += 1
        self._persist_session(session_id)

    async def associate_repair_device(
        self,
        session_id: str,
        device_id: str,
        source_client_device_id: str | None = None,
    ) -> None:
        """Associate a detected device with the session (user action)."""
        from app.schemas.device_context import DeviceContext

        session = self.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        detected = next((d for d in session.detected_devices if d.id == device_id), None)
        if detected is None:
            raise ValueError(f"device {device_id!r} not in detected list")
        now = utc_now()
        session.device_context = DeviceContext.from_detected(detected, associated_at=now)
        session.device = detected.display_name
        seeded = self._seed_diagnostics_if_empty(session)
        session.state_version += 1
        self._ensure_diagnostic_card(session_id, detected.id, detected.display_name)
        event = self.emit(
            session_id,
            RealtimeEventType.REPAIR_DEVICE_ASSOCIATED,
            payload=session.device_context.model_dump(mode="json"),
            source_client_device_id=source_client_device_id,
        )
        await self.send_event_ws(session_id, event)
        if seeded:
            await self._broadcast_diagnostics_seed(
                session_id,
                source_client_device_id or device_id,
                session,
            )
        self._persist_session(session_id)

    async def activate_repair_device(
        self,
        session_id: str,
        repair_device_id: str,
        *,
        device_name: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        source_client_device_id: str | None = None,
    ) -> None:
        """Set active repair device from an existing card (detected or manual)."""
        from app.schemas.device_context import DeviceContext

        session = self.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        detected = next(
            (d for d in session.detected_devices if d.id == repair_device_id),
            None,
        )
        now = utc_now()
        if detected is not None:
            session.device_context = DeviceContext.from_detected(detected, associated_at=now)
            display_name = detected.display_name
        else:
            is_manual = repair_device_id.startswith("manual-")
            session.device_context = DeviceContext(
                id=repair_device_id,
                brand=(brand or "").strip() or None,
                model=(model or "").strip() or None,
                source="manual" if is_manual else "unknown",
                connection_type="manual" if is_manual else "unknown",
                associated_at=now,
            )
            display_name = (device_name or session.device_context.display_name).strip()
        session.device = display_name or repair_device_id
        seeded = self._seed_diagnostics_if_empty(session)
        session.state_version += 1
        self._ensure_diagnostic_card(session_id, repair_device_id, session.device)
        event = self.emit(
            session_id,
            RealtimeEventType.REPAIR_DEVICE_ASSOCIATED,
            payload=session.device_context.model_dump(mode="json"),
            source_client_device_id=source_client_device_id,
        )
        await self.send_event_ws(session_id, event)
        if seeded:
            await self._broadcast_diagnostics_seed(
                session_id,
                source_client_device_id or repair_device_id,
                session,
            )
        self._persist_session(session_id)

    async def associate_manual_repair_device(
        self,
        session_id: str,
        brand: str,
        model: str,
        source_client_device_id: str | None = None,
    ) -> str:
        """Create and associate a manual repair device entry."""
        brand_text = brand.strip()
        model_text = model.strip()
        if not brand_text and not model_text:
            raise ValueError("brand or model required")
        repair_device_id = f"manual-{uuid4().hex[:12]}"
        display_name = " ".join(part for part in (brand_text, model_text) if part)
        await self.activate_repair_device(
            session_id,
            repair_device_id,
            device_name=display_name,
            brand=brand_text or None,
            model=model_text or None,
            source_client_device_id=source_client_device_id,
        )
        return repair_device_id

    async def unassociate_repair_device(
        self,
        session_id: str,
        source_client_device_id: str | None = None,
    ) -> None:
        """Remove the associated device from the session."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        old_id = session.device_context.id if session.device_context else None
        session.device_context = None
        session.device = None
        session.state_version += 1
        event = self.emit(
            session_id,
            RealtimeEventType.REPAIR_DEVICE_UNASSOCIATED,
            payload={"device_id": old_id},
            source_client_device_id=source_client_device_id,
        )
        await self.send_event_ws(session_id, event)
        self._persist_session(session_id)

    async def handle_client_message(
        self,
        session_id: str,
        device_id: str,
        raw: dict[str, Any],
    ) -> str:
        """Process inbound client message. Returns 'ack' or 'snapshot_sent'."""
        message = ClientInboundMessage.model_validate(raw)
        if message.type == "heartbeat":
            await self.heartbeat(session_id, device_id)
            return "ack"
        if message.type == "request_snapshot":
            await self.send_snapshot_ws(session_id, device_id)
            return "snapshot_sent"
        if message.type == "assistant_status" and message.status:
            await self.set_assistant_status(
                session_id,
                message.status,
                source_device_id=device_id,
            )
            return "ack"
        if message.type == "chat_message":
            if not message.content:
                raise ValueError("content required")
            await self.add_chat_message(
                session_id,
                device_id,
                message.content,
                role=message.role,
            )
            if message.role == "user":
                from app.conversation.natural_language_service import (
                    natural_language_service,
                )

                await natural_language_service.handle_user_message(
                    session_id,
                    device_id,
                    message.content,
                )
            return "ack"
        if message.type == "diagnostic_update":
            if not message.test_id or not message.value:
                raise StateUpdateRejected(
                    "test_id and value required",
                    request_type="diagnostic_update",
                )
            await self.update_diagnostic_measurement(
                session_id,
                device_id,
                message.test_id,
                message.value,
            )
            return "ack"
        if message.type == "diagnosis_pause":
            if message.paused is None:
                raise StateUpdateRejected(
                    "paused required",
                    request_type="diagnosis_pause",
                )
            await self.set_diagnosis_paused(session_id, device_id, message.paused)
            return "ack"
        if message.type == "repair_context_update":
            await self.update_repair_context(
                session_id,
                device_id,
                device=message.device,
                issue=message.issue,
                label=message.label,
            )
            return "ack"
        if message.type == "associate_repair_device":
            if not message.repair_device_id:
                raise StateUpdateRejected(
                    "repair_device_id required",
                    request_type="associate_repair_device",
                )
            await self.associate_repair_device(
                session_id, message.repair_device_id, source_client_device_id=device_id,
            )
            return "ack"
        if message.type == "activate_repair_device":
            if not message.repair_device_id:
                raise StateUpdateRejected(
                    "repair_device_id required",
                    request_type="activate_repair_device",
                )
            await self.activate_repair_device(
                session_id,
                message.repair_device_id,
                device_name=message.device_name,
                brand=message.brand,
                model=message.model,
                source_client_device_id=device_id,
            )
            return "ack"
        if message.type == "associate_manual_repair_device":
            if not message.brand and not message.model:
                raise StateUpdateRejected(
                    "brand or model required",
                    request_type="associate_manual_repair_device",
                )
            await self.associate_manual_repair_device(
                session_id,
                brand=message.brand or "",
                model=message.model or "",
                source_client_device_id=device_id,
            )
            return "ack"
        if message.type == "unassociate_repair_device":
            await self.unassociate_repair_device(
                session_id, source_client_device_id=device_id,
            )
            return "ack"
        raise ValueError("unsupported message type")

    def connection_count(self, session_id: str | None = None) -> int:
        if session_id is None:
            return len(self._ws_connections)
        return sum(1 for c in self._ws_connections.values() if c["session_id"] == session_id)

    def attach_persistence(self, store: Any) -> None:
        """Bind SQLite (or compatible) store and restore snapshots."""
        self._persistence_store = store
        self.restore_persisted_sessions()

    def restore_persisted_sessions(self) -> None:
        store = self._persistence_store
        if store is None or not hasattr(store, "list_realtime_session_ids"):
            return
        from app.realtime.persistence import snapshot_dict_to_session

        for session_id in store.list_realtime_session_ids():
            payload = store.load_realtime_snapshot(session_id)
            if not payload:
                continue
            if session_id in self._sessions:
                continue
            self._sessions[session_id] = snapshot_dict_to_session(payload)

    def _persist_session(self, session_id: str) -> None:
        store = self._persistence_store
        if store is None or not hasattr(store, "save_realtime_snapshot"):
            return
        session = self.get_session(session_id)
        if session is None:
            return
        from app.realtime.persistence import persistable_snapshot

        store.save_realtime_snapshot(session_id, persistable_snapshot(session))


# Singleton for app lifespan
realtime_manager = RealtimeSessionManager()
