"""Typed payloads for PC Agent WebSocket transport."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentConnectionState = Literal[
    "OFFLINE",
    "CONNECTING",
    "CONNECTED",
    "REGISTERING",
    "ONLINE",
    "RECONNECTING",
    "ERROR",
]

AgentPlatform = Literal["windows", "linux", "macos", "unknown"]


class AgentCapabilities(BaseModel):
    """Declarative capabilities — not execution permission."""

    safe_test: bool = True
    windows_apps: bool = False
    alpilab_check: bool = False
    microscope: bool = False
    thermal_camera: bool = False
    multimeter: bool = False
    power_supply: bool = False


class AgentRegistrationPayload(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=128)
    agent_name: str = Field(..., min_length=1, max_length=120)
    platform: AgentPlatform = "windows"
    agent_version: str = "0.1.0"
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    status: AgentConnectionState = "ONLINE"


class AgentPresencePayload(BaseModel):
    agent_id: str
    agent_name: str
    platform: AgentPlatform = "windows"
    agent_version: str = "0.1.0"
    online: bool = True
    status: AgentConnectionState = "ONLINE"
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    last_seen: datetime | None = None


class CommandEnvelope(BaseModel):
    """Generic command envelope for future PC Agent commands."""

    command_id: str
    request_id: str
    type: str
    source: str = "alpilab_ai"
    target: str
    timestamp: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ResultEnvelope(BaseModel):
    request_id: str
    command_id: str | None = None
    agent_id: str
    tool_id: str | None = None
    success: bool
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    timestamp: str


class AgentInboundMessage(BaseModel):
    type: Literal["register", "heartbeat", "agent_test_result", "tool_execute_result", "detected_devices_update"]
    agent_id: str | None = None
    agent_name: str | None = None
    platform: AgentPlatform | None = None
    agent_version: str | None = None
    capabilities: AgentCapabilities | None = None
    status: AgentConnectionState | None = None
    request_id: str | None = None
    command_id: str | None = None
    tool_id: str | None = None
    success: bool | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    timestamp: str | None = None
    devices: list[dict[str, Any]] | None = None


class AgentOutboundMessage(BaseModel):
    type: Literal[
        "registered",
        "heartbeat_ack",
        "command",
        "error",
        "command_rejected",
    ]
    message: str | None = None
    agent_id: str | None = None
    command: CommandEnvelope | None = None
    timestamp: str | None = None
