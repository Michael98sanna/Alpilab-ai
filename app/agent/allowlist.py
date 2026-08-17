"""Command allowlist for PC Agent — V0.1 AGENT_TEST + V0.2 TOOL_EXECUTE."""

from app.agent.payloads import CommandEnvelope

ALLOWED_AGENT_COMMANDS: frozenset[str] = frozenset({"AGENT_TEST", "TOOL_EXECUTE"})


def is_command_allowed(command_type: str) -> bool:
    return command_type in ALLOWED_AGENT_COMMANDS


def reject_reason(command_type: str) -> str:
    if command_type in ALLOWED_AGENT_COMMANDS:
        return ""
    return "COMMAND_NOT_ALLOWED"
