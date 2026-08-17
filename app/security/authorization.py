"""Permission and action authorization model."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.commands import Action, Command
from app.schemas.enums import ActionRiskLevel, IntentType


class Permission(str, Enum):
    """Granular permissions for session operations."""

    READ_SESSION = "read_session"
    WRITE_MESSAGE = "write_message"
    CONTROL_TOOL = "control_tool"
    CAPTURE_IMAGE = "capture_image"
    RECORD_MEASUREMENT = "record_measurement"
    EXECUTE_DANGEROUS_ACTION = "execute_dangerous_action"


class Capability(str, Enum):
    """Capabilities granted to users or client devices."""

    SESSION_READ = "session_read"
    SESSION_WRITE = "session_write"
    TOOL_CONTROL = "tool_control"
    HARDWARE_READ = "hardware_read"
    HARDWARE_CONTROL = "hardware_control"


class ActionAuthorization(BaseModel):
    """Authorization decision for a command/action."""

    allowed: bool
    requires_confirmation: bool = False
    risk_level: ActionRiskLevel = ActionRiskLevel.SAFE
    reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


# Intent types that never require confirmation (device switch / resume)
_NO_CONFIRM_INTENTS = {
    IntentType.CONVERSATION,
    IntentType.CONTINUE_DIAGNOSIS,
    IntentType.RESUME,
    IntentType.PAUSE,
    IntentType.STOP,
}


_RISK_BY_INTENT: dict[IntentType, ActionRiskLevel] = {
    IntentType.OPEN_TOOL: ActionRiskLevel.CONFIRM_REQUIRED,
    IntentType.OPEN_APPLICATION: ActionRiskLevel.CONFIRM_REQUIRED,
    IntentType.CLOSE_TOOL: ActionRiskLevel.SAFE,
    IntentType.CAPTURE_IMAGE: ActionRiskLevel.CONFIRM_REQUIRED,
    IntentType.SAVE_MEASUREMENT: ActionRiskLevel.SAFE,
    IntentType.SHOW_SCHEMA: ActionRiskLevel.READ_ONLY,
    IntentType.RESET_DIAGNOSTIC_FLOW: ActionRiskLevel.DANGEROUS,
}


def authorize_command(command: Command) -> ActionAuthorization:
    """Classify a command without executing it."""
    intent = command.intent.type
    risk = _RISK_BY_INTENT.get(intent, ActionRiskLevel.SAFE)
    requires_confirmation = (
        risk in {ActionRiskLevel.CONFIRM_REQUIRED, ActionRiskLevel.DANGEROUS}
        and intent not in _NO_CONFIRM_INTENTS
    )
    return ActionAuthorization(
        allowed=True,
        requires_confirmation=requires_confirmation or command.requires_confirmation,
        risk_level=risk,
        reason="classified_by_intent",
    )


def authorize_action(action: Action) -> ActionAuthorization:
    """Authorize a resolved action."""
    requires_confirmation = action.risk_level in {
        ActionRiskLevel.CONFIRM_REQUIRED,
        ActionRiskLevel.DANGEROUS,
    }
    return ActionAuthorization(
        allowed=True,
        requires_confirmation=requires_confirmation,
        risk_level=action.risk_level,
        reason="classified_by_action",
    )
