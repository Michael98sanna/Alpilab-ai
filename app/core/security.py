"""Security helpers and future permission gates.

Dangerous Hub actions must never execute blindly. This module defines the
confirmation contract used by future Alpilab Hub integrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionRisk(str, Enum):
    """Risk level for Hub / integration actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ActionPermission:
    """Declarative permission metadata for a Hub capability."""

    action: str
    risk: ActionRisk
    requires_explicit_confirmation: bool
    description: str


# Future Hub actions that must never become silent remote shell equivalents.
PROTECTED_ACTIONS: dict[str, ActionPermission] = {
    "open_application": ActionPermission(
        action="open_application",
        risk=ActionRisk.MEDIUM,
        requires_explicit_confirmation=True,
        description="Open a known lab application on the Hub PC.",
    ),
    "close_application": ActionPermission(
        action="close_application",
        risk=ActionRisk.MEDIUM,
        requires_explicit_confirmation=True,
        description="Close a known lab application on the Hub PC.",
    ),
}


def requires_confirmation(action: str) -> bool:
    meta = PROTECTED_ACTIONS.get(action)
    return bool(meta and meta.requires_explicit_confirmation)
