"""Executable tool definitions for controlled PC Agent dispatch."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import ActionRiskLevel, ToolType


class ExecutableToolSpec(BaseModel):
    """Server-controlled tool registration — clients cannot define tools."""

    tool_id: str = Field(..., min_length=1, max_length=128)
    name: str
    description: str = ""
    version: str = "1.0"
    tool_type: ToolType = ToolType.GENERIC
    risk_level: ActionRiskLevel = ActionRiskLevel.SAFE
    required_capabilities: list[str] = Field(default_factory=list)
    enabled: bool = True
    allowed_argument_keys: frozenset[str] = Field(default_factory=frozenset)


def validate_tool_arguments(
    spec: ExecutableToolSpec,
    arguments: dict[str, Any],
) -> str | None:
    """Return error code if arguments invalid, else None."""
    if not isinstance(arguments, dict):
        return "INVALID_ARGUMENTS"
    keys = frozenset(arguments.keys())
    if keys != spec.allowed_argument_keys:
        return "INVALID_ARGUMENTS"
    return None


SAFE_TEST_TOOL = ExecutableToolSpec(
    tool_id="demo.safe_test",
    name="Safe Test",
    description="Executes a harmless local test on the PC Agent",
    version="1.0",
    tool_type=ToolType.GENERIC,
    risk_level=ActionRiskLevel.SAFE,
    required_capabilities=["safe_test"],
    enabled=True,
    allowed_argument_keys=frozenset(),
)
