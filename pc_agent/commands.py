"""Command handling — AGENT_TEST + TOOL_EXECUTE allowlist (V0.2)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pc_agent.tools.dispatcher import LocalToolDispatcher
from pc_agent.tools.alpilab_check_handlers import configure_alpilab_check_client
from pc_agent.tools.windows_handlers import configure_windows_app_tool
from pc_agent.windows_apps.registry import local_app_registry

ALLOWED_COMMANDS = frozenset({"AGENT_TEST", "TOOL_EXECUTE"})

_dispatcher = LocalToolDispatcher()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_allowed_command(command_type: str) -> bool:
    return command_type in ALLOWED_COMMANDS


def configure_dispatcher(capabilities: dict[str, bool]) -> None:
    _dispatcher.set_capabilities(capabilities)
    local_app_registry.reload()
    configure_windows_app_tool()
    configure_alpilab_check_client()


def handle_command(
    command: dict[str, Any],
    agent_id: str,
) -> dict[str, Any] | None:
    """
    Process an inbound command envelope.

    Returns result payload or rejection dict.
    Returns None for unknown envelope shapes.
    """
    cmd_type = str(command.get("type", ""))
    request_id = str(command.get("request_id", ""))
    command_id = command.get("command_id")

    if not request_id:
        return None

    if not is_allowed_command(cmd_type):
        return _rejection(
            result_type="agent_test_result" if cmd_type == "AGENT_TEST" else "tool_execute_result",
            agent_id=agent_id,
            request_id=request_id,
            command_id=command_id,
            tool_id=None,
            error="COMMAND_NOT_ALLOWED",
        )

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

    if cmd_type == "TOOL_EXECUTE":
        payload = command.get("payload") or {}
        tool_id = str(payload.get("tool_id", ""))
        arguments = payload.get("arguments") or {}
        return _dispatcher.dispatch(
            tool_id,
            arguments,
            request_id=request_id,
            command_id=command_id,
            agent_id=agent_id,
        )

    return None


def _rejection(
    *,
    result_type: str,
    agent_id: str,
    request_id: str,
    command_id: str | None,
    tool_id: str | None,
    error: str,
) -> dict[str, Any]:
    return {
        "type": result_type,
        "agent_id": agent_id,
        "request_id": request_id,
        "command_id": command_id,
        "tool_id": tool_id,
        "success": False,
        "result": {},
        "error": error,
        "timestamp": utc_now_iso(),
    }
