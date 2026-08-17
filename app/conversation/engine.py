"""Unified conversation and command processing."""

from datetime import datetime, timezone
from uuid import uuid4

from ai.router import AIRouter
from ai.schemas import AIRequest
from app.commands.engine import CommandEngine
from app.commands.parser import MockCommandParser
from app.realtime.events import RealtimeEventType
from app.realtime.session_manager import RealtimeSessionManager
from app.schemas.commands import ActionResult, Command
from app.schemas.enums import IntentType, MessageChannel, SessionFlowState
from app.schemas.session import ConversationMessage, RepairSessionContext
from app.schemas.session_events import SessionEvent, SessionEventType
from app.voice.interfaces import MockSpeechToText, VoiceInput


class ConversationCommandEngine:
    """
    Single engine for text and voice input.

    Conversation flows to AI; explicit commands route to CommandEngine.
    """

    def __init__(
        self,
        parser: MockCommandParser | None = None,
        command_engine: CommandEngine | None = None,
        ai_router: AIRouter | None = None,
        stt: MockSpeechToText | None = None,
        realtime: RealtimeSessionManager | None = None,
    ) -> None:
        self._parser = parser or MockCommandParser()
        self._commands = command_engine or CommandEngine()
        self._ai = ai_router or AIRouter()
        self._stt = stt or MockSpeechToText()
        self._realtime = realtime or RealtimeSessionManager()
        self._messages: list[ConversationMessage] = []
        self._session_events: list[SessionEvent] = []

    @property
    def realtime(self) -> RealtimeSessionManager:
        return self._realtime

    def handle_text(
        self,
        repair_session_id: str,
        text: str,
        user_id: str | None = None,
        client_device_id: str | None = None,
        context: RepairSessionContext | None = None,
    ) -> tuple[ConversationMessage, Command | None, ActionResult | None, str | None]:
        intent = self._parser.parse(text)
        message = self._store_message(
            repair_session_id,
            text,
            MessageChannel.TEXT,
            user_id,
            client_device_id,
        )

        if intent.type == IntentType.CONVERSATION:
            ai_text = self._ai.generate(AIRequest(prompt=text)).content
            self._emit_ai_completed(repair_session_id, ai_text, client_device_id)
            return message, None, None, ai_text

        command = self._commands.build_command(repair_session_id, intent)
        action = self._commands.resolve_action(command)
        result = self._commands.execute_mock(action)
        self._apply_flow_command(intent.type, context)
        self._log_session_event(repair_session_id, intent.type, client_device_id)
        self._realtime.emit(
            repair_session_id,
            RealtimeEventType.TOOL_STATE_CHANGED,
            {"intent": intent.type.value, "target": intent.target},
            client_device_id,
        )
        return message, command, result, None

    def handle_voice(
        self,
        repair_session_id: str,
        voice_input: VoiceInput,
        user_id: str | None = None,
        client_device_id: str | None = None,
        context: RepairSessionContext | None = None,
    ) -> tuple[ConversationMessage, Command | None, ActionResult | None, str | None]:
        transcript = self._stt.transcribe(voice_input)
        self._realtime.emit(
            repair_session_id,
            RealtimeEventType.VOICE_TRANSCRIPT,
            {"text": transcript.text},
            client_device_id,
        )
        message = self._store_message(
            repair_session_id,
            transcript.text,
            MessageChannel.VOICE,
            user_id,
            client_device_id,
        )
        # Voice transcript becomes a normal conversation/command input.
        intent = self._parser.parse(transcript.text)
        if intent.type == IntentType.CONVERSATION:
            ai_text = self._ai.generate(AIRequest(prompt=transcript.text)).content
            self._emit_ai_completed(repair_session_id, ai_text, client_device_id)
            return message, None, None, ai_text

        command = self._commands.build_command(repair_session_id, intent)
        action = self._commands.resolve_action(command)
        result = self._commands.execute_mock(action)
        self._apply_flow_command(intent.type, context)
        self._log_session_event(repair_session_id, intent.type, client_device_id)
        return message, command, result, None

    def messages_for_session(self, repair_session_id: str) -> list[ConversationMessage]:
        return [m for m in self._messages if m.repair_session_id == repair_session_id]

    def _store_message(
        self,
        repair_session_id: str,
        content: str,
        channel: MessageChannel,
        user_id: str | None,
        client_device_id: str | None,
    ) -> ConversationMessage:
        message = ConversationMessage(
            id=str(uuid4()),
            repair_session_id=repair_session_id,
            channel=channel,
            content=content,
            author_user_id=user_id,
            client_device_id=client_device_id,
            created_at=datetime.now(timezone.utc),
        )
        self._messages.append(message)
        self._session_events.append(
            SessionEvent(
                id=str(uuid4()),
                repair_session_id=repair_session_id,
                event_type=SessionEventType.MESSAGE_CREATED,
                actor_user_id=user_id,
                client_device_id=client_device_id,
                payload={"message_id": message.id, "channel": channel.value},
                created_at=datetime.now(timezone.utc),
            )
        )
        self._realtime.emit(
            repair_session_id,
            RealtimeEventType.MESSAGE_CREATED,
            {"message_id": message.id, "content": content, "channel": channel.value},
            client_device_id,
        )
        return message

    def _emit_ai_completed(
        self, repair_session_id: str, content: str, client_device_id: str | None
    ) -> None:
        self._realtime.emit(
            repair_session_id,
            RealtimeEventType.AI_RESPONSE_COMPLETED,
            {"content": content},
            client_device_id,
        )

    def _apply_flow_command(
        self, intent: IntentType, context: RepairSessionContext | None
    ) -> None:
        if context is None:
            return
        if intent == IntentType.STOP or intent == IntentType.PAUSE:
            context.flow_state = SessionFlowState.PAUSED
        elif intent in {IntentType.RESUME, IntentType.CONTINUE_DIAGNOSIS}:
            context.flow_state = SessionFlowState.RESUMED

    def _log_session_event(
        self,
        repair_session_id: str,
        intent: IntentType,
        client_device_id: str | None,
    ) -> None:
        event_map = {
            IntentType.STOP: SessionEventType.FLOW_STOPPED,
            IntentType.PAUSE: SessionEventType.SESSION_PAUSED,
            IntentType.RESUME: SessionEventType.SESSION_RESUMED,
            IntentType.CONTINUE_DIAGNOSIS: SessionEventType.SESSION_RESUMED,
            IntentType.RESET_DIAGNOSTIC_FLOW: SessionEventType.FLOW_RESET,
            IntentType.OPEN_TOOL: SessionEventType.TOOL_OPENED,
            IntentType.CLOSE_TOOL: SessionEventType.TOOL_CLOSED,
        }
        event_type = event_map.get(intent)
        if event_type is None:
            return
        self._session_events.append(
            SessionEvent(
                id=str(uuid4()),
                repair_session_id=repair_session_id,
                event_type=event_type,
                client_device_id=client_device_id,
                payload={"intent": intent.value},
                created_at=datetime.now(timezone.utc),
            )
        )
