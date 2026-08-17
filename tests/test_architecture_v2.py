"""Architecture V2 tests — session, realtime, conversation, diagnostics, security."""

from datetime import datetime, timezone

from app.commands.parser import MockCommandParser
from app.commands.engine import CommandEngine
from app.conversation.engine import ConversationCommandEngine
from app.diagnostics.anti_loop import RepeatedRecommendationDetector, should_recommend_test
from app.diagnostics.models import DiagnosticTestRecord, RecordedEvidence
from app.diagnostics.state_manager import DiagnosticStateManager
from app.realtime.events import RealtimeEventType
from app.realtime.session_manager import RealtimeSessionManager
from app.schemas.enums import (
    DiagnosticTestStatus,
    IntentType,
    MessageChannel,
    SessionFlowState,
    SessionMode,
    ToolStatus,
)
from app.schemas.session import ClientDevice, RepairSessionContext, SessionParticipant, User
from app.security.authorization import authorize_command, authorize_action
from app.session.resume import SessionResumeManager
from app.session.store import InMemorySessionStore
from app.tools.registry import ToolRegistry
from app.voice.interfaces import VoiceInput


def _seed_user_with_devices(store: InMemorySessionStore) -> tuple[User, ClientDevice, ClientDevice]:
    user = store.save_user(User(id="user-1", display_name="Tech"))
    pc = store.save_client_device(
        ClientDevice(id="pc-1", user_id=user.id, label="PC Banco")
    )
    phone = store.save_client_device(
        ClientDevice(id="phone-1", user_id=user.id, label="Smartphone")
    )
    return user, pc, phone


def test_session_persistence_model() -> None:
    store = InMemorySessionStore()
    user, pc, _ = _seed_user_with_devices(store)
    context = store.save_context(
        RepairSessionContext(
            repair_session_id="session-1",
            mode=SessionMode.GUIDED,
            flow_state=SessionFlowState.ACTIVE,
        )
    )
    participant = store.add_participant(
        SessionParticipant(
            id="part-1",
            repair_session_id="session-1",
            client_device_id=pc.id,
            user_id=user.id,
            joined_at=datetime.now(timezone.utc),
        )
    )
    loaded = store.get_context("session-1")
    assert loaded is not None
    assert loaded.mode == SessionMode.GUIDED
    assert participant.is_active is True


def test_multiple_devices_same_session() -> None:
    store = InMemorySessionStore()
    user, pc, phone = _seed_user_with_devices(store)
    resume = SessionResumeManager(store)
    store.save_context(RepairSessionContext(repair_session_id="session-1"))

    resume.join_session(
        "session-1",
        SessionParticipant(
            id="part-pc",
            repair_session_id="session-1",
            client_device_id=pc.id,
            user_id=user.id,
        ),
    )
    resume.join_session(
        "session-1",
        SessionParticipant(
            id="part-phone",
            repair_session_id="session-1",
            client_device_id=phone.id,
            user_id=user.id,
        ),
    )

    participants = store.participants_for_session("session-1")
    assert len(participants) == 2
    device_ids = {p.client_device_id for p in participants}
    assert device_ids == {pc.id, phone.id}


def test_realtime_event_creation_and_subscription() -> None:
    manager = RealtimeSessionManager()
    received: list[str] = []

    def handler(event) -> None:
        received.append(event.event_type.value)

    manager.subscribe("session-1", handler)
    event = manager.emit(
        "session-1",
        RealtimeEventType.MESSAGE_CREATED,
        {"message_id": "m1"},
        "pc-1",
    )
    assert event.event_type == RealtimeEventType.MESSAGE_CREATED
    assert received == ["MESSAGE_CREATED"]
    assert len(manager.events_for_session("session-1")) == 1


def test_message_synchronization_model() -> None:
    realtime = RealtimeSessionManager()
    engine = ConversationCommandEngine(realtime=realtime)
    engine.handle_text("session-1", "Ciao", user_id="u1", client_device_id="pc-1")
    messages = engine.messages_for_session("session-1")
    assert len(messages) == 1
    events = realtime.events_for_session("session-1")
    assert any(e.event_type == RealtimeEventType.MESSAGE_CREATED for e in events)


def test_voice_text_shared_conversation_engine() -> None:
    engine = ConversationCommandEngine()
    text_msg, _, _, ai_text = engine.handle_text(
        "session-1", "Problema ricarica", client_device_id="pc-1"
    )
    voice_msg, _, _, ai_voice = engine.handle_voice(
        "session-1",
        VoiceInput(audio_reference="audio-1"),
        client_device_id="phone-1",
    )
    assert text_msg.channel == MessageChannel.TEXT
    assert voice_msg.channel == MessageChannel.VOICE
    assert ai_text is not None
    assert ai_voice is not None
    assert len(engine.messages_for_session("session-1")) == 2


def test_command_parsing_open_tool() -> None:
    parser = MockCommandParser()
    intent = parser.parse("Apri termocamera")
    assert intent.type == IntentType.OPEN_TOOL
    assert intent.target == "thermal_camera"


def test_command_engine_mock_execution() -> None:
    parser = MockCommandParser()
    engine = CommandEngine()
    intent = parser.parse("Apri Borneo")
    command = engine.build_command("session-1", intent)
    action = engine.resolve_action(command)
    result = engine.execute_mock(action)
    assert result.success is True
    assert "borneo" in result.message.lower() or result.data.get("tool") == "borneo"


def test_diagnostic_state_transitions() -> None:
    manager = DiagnosticStateManager()
    record = manager.register_test("session-1", "VBAT")
    manager.start_test(record.id)
    updated = manager.get_test(record.id)
    assert updated is not None
    assert updated.status == DiagnosticTestStatus.IN_PROGRESS

    evidence = RecordedEvidence(value=3.81, unit="V", source="multimeter")
    completed = manager.complete_test(
        record.id, DiagnosticTestStatus.PASSED, evidence=evidence
    )
    assert completed.status == DiagnosticTestStatus.PASSED
    assert completed.evidence is not None
    assert completed.evidence.value == 3.81


def test_repeated_test_prevention() -> None:
    manager = DiagnosticStateManager()
    record = manager.register_test("session-1", "VBAT")
    manager.complete_test(
        record.id,
        DiagnosticTestStatus.PASSED,
        evidence=RecordedEvidence(value=3.81, unit="V"),
    )
    assert manager.recommend_next_test("session-1", "VBAT") is False

    detector = RepeatedRecommendationDetector(max_repeats=2)
    for _ in range(2):
        detector.record_recommendation("session-1", "VBAT")
    assert detector.is_repeated("session-1", "VBAT") is True

    pending = DiagnosticTestRecord(
        id="t1",
        repair_session_id="session-1",
        name="USB",
        status=DiagnosticTestStatus.PENDING,
    )
    assert should_recommend_test(pending) is True


def test_interrupt_and_resume_flow() -> None:
    context = RepairSessionContext(repair_session_id="session-1")
    engine = ConversationCommandEngine()
    _, cmd_stop, result_stop, _ = engine.handle_text(
        "session-1", "Fermati", context=context
    )
    assert cmd_stop is not None
    assert result_stop is not None
    assert result_stop.success is True
    assert context.flow_state == SessionFlowState.PAUSED

    _, cmd_resume, result_resume, _ = engine.handle_text(
        "session-1", "Continua diagnosi", context=context
    )
    assert cmd_resume is not None
    assert result_resume is not None
    assert context.flow_state == SessionFlowState.RESUMED


def test_session_event_log() -> None:
    engine = ConversationCommandEngine()
    engine.handle_text("session-1", "Apri termocamera", client_device_id="pc-1")
    events = engine._session_events
    assert any(e.event_type.value == "tool_opened" for e in events)


def test_tool_abstraction_registry() -> None:
    registry = ToolRegistry()
    tool = registry.get("thermal_camera")
    assert tool is not None
    assert tool.name == "Termocamera"
    updated = registry.set_status("thermal_camera", ToolStatus.OPEN)
    assert updated is not None
    assert updated.status == ToolStatus.OPEN


def test_authorization_model() -> None:
    parser = MockCommandParser()
    command_engine = CommandEngine()
    intent = parser.parse("Apri termocamera")
    command = command_engine.build_command("session-1", intent)
    auth = authorize_command(command)
    assert auth.allowed is True
    assert auth.requires_confirmation is True
    assert auth.risk_level.value == "confirm_required"

    action = command_engine.resolve_action(command)
    action_auth = authorize_action(action)
    assert action_auth.requires_confirmation is True


def test_automatic_resume_single_active_session() -> None:
    store = InMemorySessionStore()
    user, pc, phone = _seed_user_with_devices(store)
    resume = SessionResumeManager(store)
    store.save_context(RepairSessionContext(repair_session_id="session-1"))
    resume.join_session(
        "session-1",
        SessionParticipant(
            id="p1",
            repair_session_id="session-1",
            client_device_id=pc.id,
            user_id=user.id,
        ),
    )

    # Switch device — same session, no new repair session created.
    resume.join_session(
        "session-1",
        SessionParticipant(
            id="p2",
            repair_session_id="session-1",
            client_device_id=phone.id,
            user_id=user.id,
        ),
    )
    auto = resume.resume_for_user(user.id)
    assert auto is not None
    assert auto.repair_session_id == "session-1"
