"""Session persistence and multi-device participation models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .enums import ClientPlatform, MessageChannel, SessionFlowState, SessionMode


class User(BaseModel):
    """Laboratory user (technician)."""

    id: str
    display_name: str
    email: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClientDevice(BaseModel):
    """A connected client: PC, smartphone, or tablet."""

    id: str
    user_id: str
    platform: ClientPlatform = ClientPlatform.UNKNOWN
    label: str | None = None
    user_agent: str | None = None
    last_seen_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionParticipant(BaseModel):
    """Links a client device to an active repair session."""

    id: str
    repair_session_id: str
    client_device_id: str
    user_id: str
    joined_at: datetime | None = None
    left_at: datetime | None = None
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepairSessionContext(BaseModel):
    """
    Runtime context for a repair session across devices.

    The repair session entity itself remains in repair.py; this model tracks
    multi-device state, mode, and flow control without binding to one client.
    """

    repair_session_id: str
    mode: SessionMode = SessionMode.FREE
    flow_state: SessionFlowState = SessionFlowState.ACTIVE
    active_participant_ids: list[str] = Field(default_factory=list)
    last_active_client_device_id: str | None = None
    last_activity_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationMessage(BaseModel):
    """Unified message for text and voice (post-transcription) conversation."""

    id: str
    repair_session_id: str
    channel: MessageChannel = MessageChannel.TEXT
    content: str
    author_user_id: str | None = None
    client_device_id: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
