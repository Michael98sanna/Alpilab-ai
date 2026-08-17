"""Authorization for executable tool dispatch to PC Agent."""

from __future__ import annotations

from app.agent.payloads import AgentCapabilities
from app.schemas.enums import ActionRiskLevel
from app.security.authorization import ActionAuthorization
from app.tools.executable import ExecutableToolSpec


_AUTO_EXECUTE_RISK = {ActionRiskLevel.READ_ONLY, ActionRiskLevel.SAFE}


def _is_auto_executable(tool: ExecutableToolSpec) -> bool:
    if tool.risk_level in _AUTO_EXECUTE_RISK:
        return True
    # V0.3: Windows app open tools are CONFIRM_REQUIRED (launch external software).
    # UI confirmation is deferred; dev/test endpoints may auto-execute until then.
    if tool.tool_id.startswith("windows.") and tool.tool_id.endswith(".open"):
        return tool.risk_level == ActionRiskLevel.CONFIRM_REQUIRED
    return False


def authorize_tool_execution(
    tool: ExecutableToolSpec,
    agent_capabilities: AgentCapabilities,
) -> ActionAuthorization:
    """Verify tool may be dispatched to the target agent."""
    if not tool.enabled:
        return ActionAuthorization(
            allowed=False,
            risk_level=tool.risk_level,
            reason="tool_disabled",
            metadata={"error": "TOOL_DISABLED"},
        )

    if not _is_auto_executable(tool):
        return ActionAuthorization(
            allowed=False,
            requires_confirmation=True,
            risk_level=tool.risk_level,
            reason="risk_level_not_auto_executable",
            metadata={"error": "AUTHORIZATION_DENIED"},
        )

    cap_map = agent_capabilities.model_dump()
    for required in tool.required_capabilities:
        if not cap_map.get(required, False):
            return ActionAuthorization(
                allowed=False,
                risk_level=tool.risk_level,
                reason="capability_missing",
                metadata={"error": "CAPABILITY_MISSING", "capability": required},
            )

    return ActionAuthorization(
        allowed=True,
        requires_confirmation=False,
        risk_level=tool.risk_level,
        reason="authorized",
    )
