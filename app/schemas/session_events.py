"""Session event log models for sync, audit, and anti-loop."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SessionEventType(str, Enum):
    """Canonical session event types."""

    DEVICE_IDENTIFIED = "device_identified"
    MESSAGE_CREATED = "message_created"
    MESSAGE_UPDATED = "message_updated"
    MEASUREMENT_RECORDED = "measurement_recorded"
    IMAGE_CAPTURED = "image_captured"
    DIAGNOSTIC_TEST_COMPLETED = "diagnostic_test_completed"
    AI_HYPOTHESIS_UPDATED = "ai_hypothesis_updated"
    TOOL_OPENED = "tool_opened"
    TOOL_CLOSED = "tool_closed"
    SESSION_PAUSED = "session_paused"
    SESSION_RESUMED = "session_resumed"
    SESSION_CREATED = "session_created"
    SESSION_UPDATED = "session_updated"
    FLOW_STOPPED = "flow_stopped"
    FLOW_RESET = "flow_reset"


class SessionEvent(BaseModel):
    """Immutable session event log entry."""

    id: str
    repair_session_id: str
    event_type: SessionEventType
    actor_user_id: str | None = None
    client_device_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
