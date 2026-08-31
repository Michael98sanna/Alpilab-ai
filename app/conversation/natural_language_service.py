"""Natural language chat → intent → tool execution pipeline (V0.4)."""

from __future__ import annotations

import logging
from typing import Any

from app.agent.registry import agent_registry
from app.agent.tool_executor import ToolExecutionError, tool_execution_service
from app.commands.engine import CommandEngine
from app.commands.natural_language_parser import (
    CONFIDENCE_THRESHOLD,
    NaturalLanguageCommandParser,
    ParseOutcome,
)
from app.commands.intent_models import IntentType as SemanticIntentType
from app.commands.intent_parser_v2 import HashEmbedder, SemanticIntentParser
from app.commands.tool_resolution import APPLICATION_TOOL_MAP, resolve_tool_id
from app.conversation.alpilab_check_context import (
    apply_product_search_context,
    format_product_label,
)
from app.conversation.alpilab_check_followup import (
    FollowUpOutcome,
    resolve_product_followup,
)
from app.conversation.alpilab_check_messages import (
    format_get_product_response,
    format_search_products_response,
)
from app.conversation.user_messages import error_message, success_message
from app.schemas.commands import Intent
from app.schemas.enums import IntentType as SchemaIntentType
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
        semantic_parser: SemanticIntentParser | None = None,
    ) -> None:
        self._parser = parser or NaturalLanguageCommandParser()
        self._command_engine = command_engine or CommandEngine()
        self._semantic_parser = semantic_parser or SemanticIntentParser(
            embedder=HashEmbedder()
        )

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
            session = realtime_manager.get_session(session_id)
            followup = resolve_product_followup(
                text,
                session.product_search_context if session else None,
            )
            if followup.outcome == FollowUpOutcome.ACTION and followup.intent is not None:
                logger.info(
                    "[INTENT] contextual follow-up target=%s product_index=%s",
                    followup.intent.target,
                    followup.product_index,
                )
                await self._dispatch_tool_intent(
                    realtime_manager,
                    session_id,
                    device_id,
                    followup.intent,
                    followup_detail_focus=followup.detail_focus,
                    followup_product_index=followup.product_index,
                )
                return
            if followup.outcome == FollowUpOutcome.SELECTION and followup.message:
                logger.info(
                    "[INTENT] product selection product_index=%s",
                    followup.product_index,
                )
                await self._reply(
                    realtime_manager,
                    session_id,
                    device_id,
                    followup.message,
                )
                await realtime_manager.set_assistant_status(
                    session_id, "IDLE", source_device_id=device_id
                )
                return
            if followup.outcome == FollowUpOutcome.CLARIFICATION and followup.message:
                await self._reply(
                    realtime_manager,
                    session_id,
                    device_id,
                    followup.message,
                )
                await realtime_manager.set_assistant_status(
                    session_id, "IDLE", source_device_id=device_id
                )
                return

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

        if parsed.outcome in {
            ParseOutcome.AMBIGUOUS,
            ParseOutcome.UNKNOWN_APPLICATION,
        }:
            semantic = self._semantic_parser.parse(text)
            if semantic.intent == SemanticIntentType.CLARIFY:
                options = semantic.options or []
                options_text = "\n".join(
                    f"- {opt.label} ({opt.confidence:.0%})" for opt in options
                )
                await self._reply(
                    realtime_manager,
                    session_id,
                    device_id,
                    f"Non sono sicuro. Quale intendi?\n{options_text}",
                )
                await realtime_manager.set_assistant_status(
                    session_id, "IDLE", source_device_id=device_id
                )
                return

            if semantic.intent == SemanticIntentType.OPEN_APPLICATION and semantic.tool_id:
                target = self._semantic_target_for_tool(semantic.tool_id)
                if target is not None:
                    intent = Intent(
                        type=SchemaIntentType.OPEN_APPLICATION,
                        target=target,
                        raw_text=text,
                        confidence=semantic.confidence,
                    )
                    await self._dispatch_tool_intent(
                        realtime_manager,
                        session_id,
                        device_id,
                        intent,
                    )
                    return

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

        await self._dispatch_tool_intent(
            realtime_manager,
            session_id,
            device_id,
            parsed.intent,
        )

    async def _dispatch_tool_intent(
        self,
        realtime_manager: Any,
        session_id: str,
        device_id: str,
        intent: Intent,
        *,
        followup_detail_focus: str | None = None,
        followup_product_index: int | None = None,
    ) -> None:
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
                dict(intent.parameters),
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

        if result.success:
            if tool_id == "alpilab_check.search_products" and session is not None:
                apply_product_search_context(session, result.result)

            product_label = None
            if (
                followup_product_index is not None
                and session is not None
                and session.product_search_context is not None
                and 0 <= followup_product_index < len(session.product_search_context.items)
            ):
                product_label = format_product_label(
                    session.product_search_context.items[followup_product_index]
                )

            msg = self._success_message_for_tool(
                tool_id,
                result.result,
                detail_focus=followup_detail_focus,
                product_label=product_label,
                product_search_context=(
                    session.product_search_context if session is not None else None
                ),
            )
            logger.info("[RESULT] success=True tool=%s summary=%s", tool_id, msg)
            logger.info("[TOOL] %s", tool_id)
            await self._reply(realtime_manager, session_id, device_id, msg)
            await realtime_manager.set_assistant_status(
                session_id,
                "SPEAKING",
                source_device_id=device_id,
            )
            await realtime_manager.set_assistant_status(
                session_id, "IDLE", source_device_id=device_id
            )
            return

        code = result.error or "TOOL_EXECUTION_FAILED"
        msg = error_message(code)
        logger.info(
            "[RESULT] success=False tool=%s error=%s summary=%s",
            tool_id,
            code,
            msg,
        )
        logger.info("[TOOL] %s", tool_id)
        await self._reply(realtime_manager, session_id, device_id, msg)
        await realtime_manager.set_assistant_status(
            session_id, "ERROR", source_device_id=device_id
        )

    def _success_message_for_tool(
        self,
        tool_id: str,
        payload: dict,
        *,
        detail_focus: str | None = None,
        product_label: str | None = None,
        product_search_context: Any = None,
    ) -> str:
        if tool_id == "windows.3utools.open":
            dry_run = payload.get("mode") == "dry_run"
            return success_message(dry_run=dry_run)
        if tool_id == "windows.alpilab_check.open":
            if payload.get("already_running"):
                return "Alpilab Check è già aperto."
            dry_run = payload.get("mode") == "dry_run"
            if dry_run:
                return "Alpilab Check: verifica dry-run completata."
            return "Alpilab Check avviato."
        if tool_id == "alpilab_check.search_products":
            return format_search_products_response(
                payload if isinstance(payload, dict) else {},
                context=product_search_context,
            )
        if tool_id == "alpilab_check.get_product":
            return format_get_product_response(
                payload if isinstance(payload, dict) else {},
                detail_focus=detail_focus,
                product_label=product_label,
            )
        if tool_id == "alpilab_check.search_invoices":
            items = payload.get("items") if isinstance(payload, dict) else None
            if isinstance(items, list):
                if not items:
                    return "Non ho trovato fatture per questa ricerca."
                sample = [str(i.get("code") or i.get("id") or "n/d") for i in items[:3] if isinstance(i, dict)]
                return f"Ho trovato {len(items)} fatture: {', '.join(sample)}."
        if tool_id == "alpilab_check.get_invoice":
            if isinstance(payload, dict) and payload:
                iid = payload.get("id", "n/d")
                return f"Dettaglio fattura {iid} recuperato."
            return "Non ho trovato dettagli per la fattura richiesta."
        return "Richiesta completata."

    async def _reply(self, realtime_manager, session_id: str, device_id: str, content: str) -> None:
        await realtime_manager.add_chat_message(
            session_id,
            device_id,
            content,
            role="assistant",
        )

    @staticmethod
    def _semantic_target_for_tool(tool_id: str) -> str | None:
        for target, mapped_tool_id in APPLICATION_TOOL_MAP.items():
            if mapped_tool_id == tool_id:
                return target
        return None


natural_language_service = NaturalLanguageCommandService()
