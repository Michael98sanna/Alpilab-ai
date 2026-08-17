"""Local executable tool definitions for PC Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Awaitable

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class LocalToolSpec:
    tool_id: str
    required_capability: str
    allowed_argument_keys: frozenset[str]
    handler: ToolHandler


def execute_safe_test(_arguments: dict[str, Any]) -> dict[str, Any]:
    """Harmless tool — no OS interaction."""
    return {
        "status": "ok",
        "message": "Alpilab PC Agent tool execution works",
    }
