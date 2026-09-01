"""Typed realtime event payloads for WebSocket transport."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.agent.payloads import AgentPresencePayload

MAX_MESSAGE_LENGTH = 4000

DeviceType = Literal["pc", "phone", "tablet"]
AssistantStatus = Literal[
    "IDLE",
    "LISTENING",
    "THINKING",
    "SPEAKING",
    "WORKING",
    "WARNING",
    "ERROR",
]
MessageRole = Literal["user", "assistant", "system"]


class ChatMessagePayload(BaseModel):
    message_id: str
    session_id: str
    device_id: str | None = None
    role: MessageRole
    content: str
    timestamp: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("content must not be empty")
        if len(trimmed) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"content exceeds {MAX_MESSAGE_LENGTH} characters")
        return trimmed


class AssistantStatusPayload(BaseModel):
    status: AssistantStatus
    label: str | None = None


class DevicePresencePayload(BaseModel):
    device_id: str
    device_type: DeviceType
    device_name: str
    online: bool
    connected_at: datetime | None = None
    last_seen: datetime | None = None


class RepairContextPayload(BaseModel):
    id: str
    label: str
    device: str | None = None
    issue: str | None = None
    status: str = "active"
    diagnosis_label: str = ""


class DiagnosticTestPayload(BaseModel):
    id: str
    name: str
    value: str | None = None
    status: str = "PENDING"


class SessionSnapshotPayload(BaseModel):
    session: RepairContextPayload
    participants: list[DevicePresencePayload]
    conversation: list[ChatMessagePayload]
    repair_context: RepairContextPayload
    diagnostic_state: list[DiagnosticTestPayload]
    assistant_status: AssistantStatus = "IDLE"
    state_version: int = 0
    pc_agent: AgentPresencePayload | None = None
    device_context: dict[str, Any] | None = None
    detected_devices: list[dict[str, Any]] = Field(default_factory=list)


class SessionStateUpdatedPayload(BaseModel):
    event_id: str
    session_id: str
    timestamp: str
    source_device_id: str
    state_version: int
    changes: dict[str, Any]


class StateUpdateRejectedPayload(BaseModel):
    reason: str
    request_type: str | None = None
    state_version: int


class RepairDevicePayload(BaseModel):
    """Payload for REPAIR_DEVICE_* events."""

    device_id: str
    brand: str | None = None
    model: str | None = None
    variant: str | None = None
    serial_number: str | None = None
    imei: str | None = None
    connection_type: str | None = None
    source: str | None = None


class ClientInboundMessage(BaseModel):
    type: Literal[
        "chat_message",
        "heartbeat",
        "assistant_status",
        "diagnostic_update",
        "diagnosis_pause",
        "repair_context_update",
        "request_snapshot",
        "associate_repair_device",
        "associate_manual_repair_device",
        "activate_repair_device",
        "unassociate_repair_device",
    ]
    content: str | None = None
    role: MessageRole = "user"
    status: AssistantStatus | None = None
    test_id: str | None = None
    value: str | None = None
    paused: bool | None = None
    device: str | None = None
    issue: str | None = None
    label: str | None = None
    repair_device_id: str | None = None
    brand: str | None = None
    model: str | None = None
    device_name: str | None = None


class WsEnvelope(BaseModel):
    type: Literal["event", "snapshot", "error", "ack"]
    event: dict[str, Any] | None = None
    payload: dict[str, Any] | None = None
    message: str | None = None
