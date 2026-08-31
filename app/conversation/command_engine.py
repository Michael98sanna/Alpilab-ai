"""Semantic command processing for conversation flows."""

from __future__ import annotations

import logging
from typing import Any

from app.agent.tool_executor import ToolExecutionError, tool_execution_service
from app.commands.engine import CommandEngine
from app.commands.intent_models import IntentResult, IntentType
from app.commands.intent_parser_v2 import HashEmbedder, SemanticIntentParser
from app.commands.tool_resolution import APPLICATION_TOOL_MAP
from app.schemas.commands import Intent
from app.schemas.enums import IntentType as SchemaIntentType
from app.schemas.session import RepairSessionContext
from app.tools.registry import ToolRegistry, default_tool_registry

logger = logging.getLogger(__name__)

EXECUTABLE_TOOL_IDS = frozenset(APPLICATION_TOOL_MAP.values())
TOOL_ID_TO_TARGET = {tool_id: target for target, tool_id in APPLICATION_TOOL_MAP.items()}


class ConversationCommandEngine:
    """
    Process text/voice input through semantic intent parsing.

    Returns structured results for conversation, clarification, or tool execution.
    """

    def __init__(
        self,
        intent_parser: SemanticIntentParser | None = None,
        command_engine: CommandEngine | None = None,
        tool_registry: ToolRegistry | None = None,
        stt: Any | None = None,
        tts: Any | None = None,
    ) -> None:
        self.intent_parser = intent_parser or SemanticIntentParser(
            embedder=HashEmbedder()
        )
        self.command_engine = command_engine or CommandEngine(
            tool_registry=tool_registry or default_tool_registry
        )
        self.tool_registry = tool_registry or default_tool_registry
        self.stt = stt or self._default_stt()
        self.tts = tts or self._default_tts()

    @staticmethod
    def _default_stt() -> Any:
        from app.voice.speech_to_text import DeterministicSTT

        return DeterministicSTT()

    @staticmethod
    def _default_tts() -> Any:
        from app.voice.text_to_speech import DeterministicTTS

        return DeterministicTTS()

    def parse_intent(self, user_text: str) -> IntentResult:
        """Parse user text into a semantic intent result."""
        return self.intent_parser.parse(user_text)

    async def process_user_input(
        self,
        user_text: str,
        session: RepairSessionContext | None,
        *,
        session_id: str,
        device_id: str,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Process text input and return conversation, clarification, or tool result.
        """
        _ = session  # Reserved for future RAG / context-aware routing
        intent_result = self.intent_parser.parse(user_text)

        if intent_result.intent == IntentType.UNKNOWN:
            from ai.router import AIRouter
            from ai.schemas import AIRequest

            reply = AIRouter().generate(AIRequest(prompt=user_text)).content
            return {
                "type": "conversation",
                "message": reply,
            }

        if intent_result.intent == IntentType.CLARIFY:
            options = intent_result.options or []
            options_text = "\n".join(
                f"- {opt.label} ({opt.confidence:.0%})" for opt in options
            )
            return {
                "type": "clarification",
                "message": f"Non sono sicuro. Quale intendi?\n{options_text}",
                "options": intent_result.options_as_dicts(),
            }

        if intent_result.intent == IntentType.RUN_DIAGNOSTIC:
            return {
                "type": "diagnostic",
                "message": "Avvio flusso diagnostico.",
                "confidence": intent_result.confidence,
            }

        if intent_result.intent in {
            IntentType.OPEN_APPLICATION,
            IntentType.CLOSE_APPLICATION,
        }:
            return await self._execute_tool_intent(
                intent_result,
                session_id=session_id,
                device_id=device_id,
                agent_id=agent_id,
            )

        return {
            "type": "conversation",
            "message": "Non ho capito la richiesta.",
        }

    async def process_voice_input(
        self,
        audio_bytes: bytes,
        session: RepairSessionContext | None,
        *,
        session_id: str,
        device_id: str,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Process voice input: STT → command/conversation → optional TTS response.
        """
        listening = {"status": "listening", "message": "Ascoltando..."}

        user_text = await self.stt.transcribe_stream(audio_bytes)
        response = await self.process_user_input(
            user_text,
            session,
            session_id=session_id,
            device_id=device_id,
            agent_id=agent_id,
        )

        message = response.get("message")
        if isinstance(message, str) and message.strip():
            audio_response = await self.tts.speak(message)
            return {
                **response,
                "listening": listening,
                "transcript": user_text,
                "text": message,
                "audio": audio_response,
            }

        return {
            **response,
            "listening": listening,
            "transcript": user_text,
        }

    async def _execute_tool_intent(
        self,
        intent_result: IntentResult,
        *,
        session_id: str,
        device_id: str,
        agent_id: str | None,
    ) -> dict[str, Any]:
        tool_id = intent_result.tool_id
        if not tool_id:
            return {
                "type": "error",
                "message": "Tool non identificato.",
            }

        if tool_id not in EXECUTABLE_TOOL_IDS:
            label = self.tool_registry.get_tool_label(tool_id)
            return {
                "type": "error",
                "message": f"L'applicazione {label} non è ancora eseguibile da qui.",
            }

        target = TOOL_ID_TO_TARGET.get(tool_id)
        if target is None:
            return {
                "type": "error",
                "message": "Tool non mappato.",
            }

        schema_intent = Intent(
            type=SchemaIntentType.OPEN_APPLICATION,
            target=target,
            raw_text=tool_id,
            confidence=intent_result.confidence,
        )
        command = self.command_engine.build_command(session_id, schema_intent)
        from app.security.authorization import authorize_command

        auth = authorize_command(command)
        if not auth.allowed:
            return {
                "type": "error",
                "message": "Operazione non autorizzata.",
            }

        if agent_id is None:
            return {
                "type": "error",
                "message": "Agente PC non connesso.",
            }

        tool_spec = self.tool_registry.get_executable(tool_id)
        if tool_spec is None:
            return {
                "type": "error",
                "message": "Tool non trovato.",
            }

        try:
            result = await tool_execution_service.execute_tool(
                session_id,
                agent_id,
                tool_id,
                {},
            )
        except ToolExecutionError as exc:
            logger.warning("Semantic tool execution failed: %s", exc.error_code)
            return {
                "type": "error",
                "message": exc.error_code,
            }

        return {
            "type": "tool_result",
            "tool_id": tool_id,
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "device_id": device_id,
        }
