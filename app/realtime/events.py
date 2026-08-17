"""Realtime event types and payloads for multi-device synchronization."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RealtimeEventType(str, Enum):
    """Events broadcast to connected session clients."""

    SESSION_CREATED = "SESSION_CREATED"
    SESSION_UPDATED = "SESSION_UPDATED"
    MESSAGE_CREATED = "MESSAGE_CREATED"
    MESSAGE_UPDATED = "MESSAGE_UPDATED"
    AI_RESPONSE_STARTED = "AI_RESPONSE_STARTED"
    AI_RESPONSE_CHUNK = "AI_RESPONSE_CHUNK"
    AI_RESPONSE_COMPLETED = "AI_RESPONSE_COMPLETED"
    VOICE_TRANSCRIPT = "VOICE_TRANSCRIPT"
    MEASUREMENT_CREATED = "MEASUREMENT_CREATED"
    IMAGE_CREATED = "IMAGE_CREATED"
    IMAGE_UPDATED = "IMAGE_UPDATED"
    ANNOTATION_CREATED = "ANNOTATION_CREATED"
    DIAGNOSTIC_TEST_UPDATED = "DIAGNOSTIC_TEST_UPDATED"
    TOOL_STATE_CHANGED = "TOOL_STATE_CHANGED"
    DEVICE_CONNECTED = "DEVICE_CONNECTED"
    DEVICE_DISCONNECTED = "DEVICE_DISCONNECTED"
    SESSION_RESUMED = "SESSION_RESUMED"


class RealtimeEvent(BaseModel):
    """Realtime envelope sent to subscribed clients."""

    id: str
    repair_session_id: str
    event_type: RealtimeEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    emitted_at: datetime | None = None
    source_client_device_id: str | None = None
