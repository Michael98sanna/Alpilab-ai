"""Command handling — AGENT_TEST allowlist only (V0.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ALLOWED_COMMANDS = frozenset({"AGENT_TEST"})


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_allowed_command(command_type: str) -> bool:
    return command_type in ALLOWED_COMMANDS


def handle_command(
    command: dict[str, Any],
    agent_id: str,
) -> dict[str, Any] | None:
    """
    Process an inbound command envelope.

    Returns agent_test_result payload or rejection result dict.
    Returns None for unknown envelope shapes.
    """
    cmd_type = str(command.get("type", ""))
    request_id = str(command.get("request_id", ""))
    command_id = command.get("command_id")

    if not request_id:
        return None

    if not is_allowed_command(cmd_type):
        return {
            "type": "agent_test_result",
            "agent_id": agent_id,
            "request_id": request_id,
            "command_id": command_id,
            "success": False,
            "result": {},
            "error": "COMMAND_NOT_ALLOWED",
            "timestamp": utc_now_iso(),
        }

    if cmd_type == "AGENT_TEST":
        return {
            "type": "agent_test_result",
            "agent_id": agent_id,
            "request_id": request_id,
            "command_id": command_id,
            "success": True,
            "result": {"message": "pong", "idle": True},
            "error": None,
            "timestamp": utc_now_iso(),
        }

    return None
