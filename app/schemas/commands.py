"""Command and intent models for the Command Engine."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .enums import ActionRiskLevel, IntentType


class Intent(BaseModel):
    """Parsed intent from user text or voice transcript."""

    type: IntentType
    target: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    raw_text: str = ""
    confidence: float = 1.0


class Command(BaseModel):
    """Resolved command ready for authorization and execution."""

    id: str
    repair_session_id: str
    intent: Intent
    risk_level: ActionRiskLevel = ActionRiskLevel.SAFE
    requires_confirmation: bool = False
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Action(BaseModel):
    """Concrete action to execute (Hub, tool, or internal)."""

    id: str
    command_id: str
    action_type: str
    target: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    risk_level: ActionRiskLevel = ActionRiskLevel.SAFE


class ActionResult(BaseModel):
    """Outcome of an action attempt."""

    action_id: str
    success: bool
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime | None = None
