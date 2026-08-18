"""Natural language chat → intent → tool execution pipeline (V0.4)."""

from __future__ import annotations

import logging

from app.agent.registry import agent_registry
from app.agent.tool_executor import ToolExecutionError, tool_execution_service
from app.commands.engine import CommandEngine
from app.commands.natural_language_parser import (
    CONFIDENCE_THRESHOLD,
    NaturalLanguageCommandParser,
    ParseOutcome,
)
from app.commands.tool_resolution import resolve_tool_id
from app.conversation.user_messages import error_message, success_message
from app.security.tool_authorization import authorize_tool_execution
from app.tools.registry import default_tool_registry

logger = logging.getLogger(__name__)


class NaturalLanguageCommandService:
    """
    Backend-only NL dispatch: text → Intent → Authorization → ToolRegistry → AgentGateway.

    Never constructs paths, shell commands, or arbitrary executables from user text.
    """

    def __init__(
        self,
        parser: NaturalLanguageCommandParser | None = None,
        command_engine: CommandEngine | None = None,
    ) -> None:
        self._parser = parser or NaturalLanguageCommandParser()
        self._command_engine = command_engine or CommandEngine()

    async def handle_user_message(
        self,
        session_id: str,
        device_id: str,
        text: str,
    ) -> None:
        from app.realtime.session_manager import realtime_manager

        logger.info("[COMMAND] Received natural language command session=%s", session_id)
        parsed = self._parser.parse(text)

        if parsed.outcome == ParseOutcome.CONVERSATION:
            logger.info("[INTENT] CONVERSATION — local AI router (no tool dispatch)")
            await realtime_manager.set_assistant_status(
                session_id,
                "THINKING",
                source_device_id=device_id,
            )
            from ai.router import AIRouter
            from ai.schemas import AIRequest

            reply = AIRouter().generate(AIRequest(prompt=text)).content
            await self._reply(realtime_manager, session_id, device_id, reply)
            await realtime_manager.set_assistant_status(
                session_id,
                "SPEAKING",
                source_device_id=device_id,
            )
            await realtime_manager.set_assistant_status(
                session_id, "IDLE", source_device_id=device_id
            )
            return

        if parsed.confidence < CONFIDENCE_THRESHOLD:
            await self._reply(
                realtime_manager,
                session_id,
                device_id,
                "Puoi chiarire la richiesta?",
            )
            return

        await realtime_manager.set_assistant_status(
            session_id,
            "THINKING",
            source_device_id=device_id,
        )

        if parsed.outcome == ParseOutcome.AMBIGUOUS:
            await self._reply(
                realtime_manager,
                session_id,
                device_id,
                parsed.clarification or error_message("AMBIGUOUS_COMMAND"),
            )
            await realtime_manager.set_assistant_status(
                session_id, "IDLE", source_device_id=device_id
            )
            return

        if parsed.outcome in {
            ParseOutcome.COMMAND_NOT_SUPPORTED,
            ParseOutcome.UNKNOWN_APPLICATION,
            ParseOutcome.INVALID_COMMAND,
        }:
            code = parsed.error_code or parsed.outcome.value.upper()
            logger.info("[INTENT] rejected error=%s", code)
            await self._reply(realtime_manager, session_id, device_id, error_message(code))
            await realtime_manager.set_assistant_status(
                session_id, "IDLE", source_device_id=device_id
            )
            return

        if parsed.outcome != ParseOutcome.ACTION_COMMAND or parsed.intent is None:
            await realtime_manager.set_assistant_status(
                session_id, "IDLE", source_device_id=device_id
            )
            return

        intent = parsed.intent
        logger.info(
            "[INTENT] %s target=%s confidence=%s",
            intent.type.value,
            intent.target,
            intent.confidence,
        )

        tool_id = resolve_tool_id(intent)
        if tool_id is None:
            await self._reply(
                realtime_manager,
                session_id,
                device_id,
                error_message("UNKNOWN_APPLICATION"),
            )
            await realtime_manager.set_assistant_status(
                session_id, "IDLE", source_device_id=device_id
            )
            return

        logger.info("[COMMAND] Resolved tool=%s", tool_id)

        command = self._command_engine.build_command(session_id, intent)
        from app.security.authorization import authorize_command

        auth_cmd = authorize_command(command)
        if not auth_cmd.allowed:
            await self._reply(
                realtime_manager,
                session_id,
                device_id,
                error_message("AUTHORIZATION_DENIED"),
            )
            await realtime_manager.set_assistant_status(
                session_id, "IDLE", source_device_id=device_id
            )
            return

        tool_spec = default_tool_registry.get_executable(tool_id)
        if tool_spec is None:
            await self._reply(
                realtime_manager,
                session_id,
                device_id,
                error_message("TOOL_NOT_FOUND"),
            )
            await realtime_manager.set_assistant_status(
                session_id, "IDLE", source_device_id=device_id
            )
            return

        session = realtime_manager.get_session(session_id)
        agent_id = None
        if session and session.pc_agent and session.pc_agent.online:
            agent_id = session.pc_agent.agent_id

        if not agent_id:
            agents = agent_registry.list_agents(session_id)
            online = [a for a in agents if a.status == "ONLINE"]
            if online:
                agent_id = online[0].agent_id

        if not agent_id:
            logger.info("[AUTH] AGENT_OFFLINE session=%s", session_id)
            await self._reply(
                realtime_manager,
                session_id,
                device_id,
                error_message("AGENT_NOT_FOUND"),
            )
            await realtime_manager.set_assistant_status(
                session_id, "ERROR", source_device_id=device_id
            )
            return

        agent = agent_registry.get(session_id, agent_id)
        if agent is None:
            await self._reply(
                realtime_manager,
                session_id,
                device_id,
                error_message("AGENT_NOT_FOUND"),
            )
            await realtime_manager.set_assistant_status(
                session_id, "ERROR", source_device_id=device_id
            )
            return

        tool_auth = authorize_tool_execution(tool_spec, agent.capabilities)
        if not tool_auth.allowed:
            code = str(tool_auth.metadata.get("error", "AUTHORIZATION_DENIED"))
            logger.info("[AUTH] denied code=%s tool=%s", code, tool_id)
            await self._reply(
                realtime_manager,
                session_id,
                device_id,
                error_message(code),
            )
            await realtime_manager.set_assistant_status(
                session_id, "ERROR", source_device_id=device_id
            )
            return

        logger.info("[AUTH] Authorized tool=%s agent=%s", tool_id, agent_id)
        await realtime_manager.set_assistant_status(
            session_id,
            "WORKING",
            source_device_id=device_id,
        )
        logger.info("[AGENT] Dispatching tool=%s", tool_id)

        try:
            result = await tool_execution_service.execute_tool(
                session_id,
                agent_id,
                tool_id,
                {},
            )
        except ToolExecutionError as exc:
            logger.warning("[RESULT] success=false error=%s", exc.error_code)
            await self._reply(
                realtime_manager,
                session_id,
                device_id,
                error_message(exc.error_code),
            )
            await realtime_manager.set_assistant_status(
                session_id, "ERROR", source_device_id=device_id
            )
            return

        dry_run = result.result.get("mode") == "dry_run"
        msg = success_message(dry_run=dry_run)
        logger.info(
            "[RESULT] success=%s tool=%s summary=%s",
            result.success,
            tool_id,
            msg,
        )
        logger.info("[TOOL] %s", tool_id)

        if result.success:
            await self._reply(realtime_manager, session_id, device_id, msg)
            await realtime_manager.set_assistant_status(
                session_id,
                "SPEAKING",
                source_device_id=device_id,
            )
            await realtime_manager.set_assistant_status(
                session_id, "IDLE", source_device_id=device_id
            )
        else:
            await self._reply(
                realtime_manager,
                session_id,
                device_id,
                error_message(result.error or "TOOL_EXECUTION_FAILED"),
            )
            await realtime_manager.set_assistant_status(
                session_id, "ERROR", source_device_id=device_id
            )

    async def _reply(self, realtime_manager, session_id: str, device_id: str, content: str) -> None:
        await realtime_manager.add_chat_message(
            session_id,
            device_id,
            content,
            role="assistant",
        )


natural_language_service = NaturalLanguageCommandService()
