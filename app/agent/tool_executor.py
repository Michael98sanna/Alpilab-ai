"""Orchestrates authorized tool execution via PC Agent."""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from app.agent.execution_store import tool_execution_store
from app.agent.gateway import agent_gateway
from app.agent.payloads import CommandEnvelope, ResultEnvelope
from app.agent.registry import agent_registry
from app.security.tool_authorization import authorize_tool_execution
from app.tools.executable import validate_tool_arguments
from app.tools.registry import ToolRegistry, default_tool_registry

logger = logging.getLogger(__name__)

DEFAULT_TOOL_TIMEOUT_SEC = 30.0


class ToolExecutionError(Exception):
    def __init__(self, error_code: str, message: str = "") -> None:
        super().__init__(message or error_code)
        self.error_code = error_code


class ToolExecutionService:
    """Authorization + registry + agent dispatch for executable tools."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self._registry = registry or default_tool_registry

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    async def execute_tool(
        self,
        session_id: str,
        agent_id: str,
        tool_id: str,
        arguments: dict | None = None,
        *,
        request_id: str | None = None,
        timeout_sec: float = DEFAULT_TOOL_TIMEOUT_SEC,
    ) -> ResultEnvelope:
        args = arguments if arguments is not None else {}

        if request_id:
            cached = tool_execution_store.get_completed(request_id)
            if cached is not None:
                return cached

        spec = self._registry.get_executable(tool_id)
        if spec is None:
            raise ToolExecutionError("TOOL_NOT_FOUND", f"unknown tool: {tool_id}")

        if not spec.enabled:
            raise ToolExecutionError("TOOL_DISABLED", f"tool disabled: {tool_id}")

        arg_error = validate_tool_arguments(spec, args)
        if arg_error:
            raise ToolExecutionError(arg_error, "invalid tool arguments")

        agent = agent_registry.get(session_id, agent_id)
        if agent is None:
            raise ToolExecutionError("AGENT_NOT_FOUND", f"agent not online: {agent_id}")

        auth = authorize_tool_execution(spec, agent.capabilities)
        if not auth.allowed:
            error = str(auth.metadata.get("error", "AUTHORIZATION_DENIED"))
            raise ToolExecutionError(error, auth.reason)

        req_id = request_id or str(uuid4())
        cmd_id = str(uuid4())

        future = tool_execution_store.register_pending(
            request_id=req_id,
            command_id=cmd_id,
            tool_id=tool_id,
            agent_id=agent_id,
            session_id=session_id,
        )

        cached_after_register = tool_execution_store.get_completed(req_id)
        if cached_after_register is not None:
            return cached_after_register

        command = await agent_gateway.send_tool_execute(
            session_id=session_id,
            agent_id=agent_id,
            tool_id=tool_id,
            arguments=args,
            request_id=req_id,
            command_id=cmd_id,
        )

        try:
            return await asyncio.wait_for(future, timeout=timeout_sec)
        except asyncio.TimeoutError as exc:
            tool_execution_store.fail_pending(req_id, "TOOL_EXECUTION_TIMEOUT")
            logger.warning(
                "Tool execution timeout session=%s agent=%s tool=%s request=%s",
                session_id,
                agent_id,
                tool_id,
                req_id,
            )
            raise ToolExecutionError("TOOL_EXECUTION_TIMEOUT", "agent did not respond in time") from exc


tool_execution_service = ToolExecutionService()
