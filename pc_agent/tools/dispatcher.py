"""Local tool dispatcher — registered tools only, no shell execution."""

from __future__ import annotations

import logging
from typing import Any

from pc_agent.tools.registry import LocalToolRegistry, local_tool_registry
from pc_agent.windows_apps.tool import WindowsAppToolError

logger = logging.getLogger(__name__)


class LocalToolDispatcher:
    """Resolves and executes only explicitly registered local tools."""

    def __init__(
        self,
        registry: LocalToolRegistry | None = None,
        *,
        capabilities: dict[str, bool] | None = None,
    ) -> None:
        self._registry = registry or local_tool_registry
        self._capabilities = capabilities or {"safe_test": True}
        self._completed: dict[str, dict[str, Any]] = {}

    def set_capabilities(self, capabilities: dict[str, bool]) -> None:
        self._capabilities = capabilities

    def dispatch(
        self,
        tool_id: str,
        arguments: dict[str, Any],
        *,
        request_id: str,
        command_id: str | None,
        agent_id: str,
    ) -> dict[str, Any]:
        if request_id in self._completed:
            return self._completed[request_id]

        spec = self._registry.get(tool_id)
        if spec is None:
            return self._result(
                request_id=request_id,
                command_id=command_id,
                agent_id=agent_id,
                tool_id=tool_id,
                success=False,
                error="TOOL_NOT_FOUND",
            )

        if not self._capabilities.get(spec.required_capability, False):
            return self._result(
                request_id=request_id,
                command_id=command_id,
                agent_id=agent_id,
                tool_id=tool_id,
                success=False,
                error="CAPABILITY_MISSING",
            )

        if not isinstance(arguments, dict):
            return self._result(
                request_id=request_id,
                command_id=command_id,
                agent_id=agent_id,
                tool_id=tool_id,
                success=False,
                error="INVALID_ARGUMENTS",
            )

        if frozenset(arguments.keys()) != spec.allowed_argument_keys:
            return self._result(
                request_id=request_id,
                command_id=command_id,
                agent_id=agent_id,
                tool_id=tool_id,
                success=False,
                error="INVALID_ARGUMENTS",
            )

        try:
            result_payload = spec.handler(arguments)
        except WindowsAppToolError as exc:
            return self._result(
                request_id=request_id,
                command_id=command_id,
                agent_id=agent_id,
                tool_id=tool_id,
                success=False,
                error=exc.code,
            )
        except Exception:
            logger.exception("Tool handler failed tool_id=%s", tool_id)
            return self._result(
                request_id=request_id,
                command_id=command_id,
                agent_id=agent_id,
                tool_id=tool_id,
                success=False,
                error="TOOL_EXECUTION_FAILED",
            )

        response = self._result(
            request_id=request_id,
            command_id=command_id,
            agent_id=agent_id,
            tool_id=tool_id,
            success=True,
            result=result_payload,
        )
        self._completed[request_id] = response
        return response

    def _result(
        self,
        *,
        request_id: str,
        command_id: str | None,
        agent_id: str,
        tool_id: str,
        success: bool,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        from pc_agent.commands import utc_now_iso

        return {
            "type": "tool_execute_result",
            "request_id": request_id,
            "command_id": command_id,
            "agent_id": agent_id,
            "tool_id": tool_id,
            "success": success,
            "result": result or {},
            "error": error,
            "timestamp": utc_now_iso(),
        }
