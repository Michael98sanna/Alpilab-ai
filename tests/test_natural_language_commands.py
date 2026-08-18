"""Natural language command tests — V0.4."""

import pytest
from fastapi.testclient import TestClient

from app.agent.execution_store import tool_execution_store
from app.agent.registry import agent_registry
from app.commands.natural_language_parser import (
    NaturalLanguageCommandParser,
    ParseOutcome,
)
from app.commands.tool_resolution import resolve_tool_id
from app.main import app
from app.schemas.enums import IntentType
from pc_agent.commands import configure_dispatcher, handle_command
from pc_agent.tools.windows_handlers import configure_windows_app_tool
from pc_agent.windows_apps.launcher import MockProcessLauncher
from pc_agent.windows_apps.models import WindowsApplicationConfig
from pc_agent.windows_apps.registry import local_app_registry
from pc_agent.windows_apps.tool import WindowsAppTool


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def parser() -> NaturalLanguageCommandParser:
    return NaturalLanguageCommandParser()


@pytest.fixture(autouse=True)
def reset_state() -> None:
    agent_registry.clear()
    tool_execution_store.clear()
    local_app_registry.set_apps({})
    from app.realtime import session_manager as sm

    sm.realtime_manager._sessions.clear()
    sm.realtime_manager._ws_connections.clear()
    sm.realtime_manager._event_log.clear()


def _agent_connect(client: TestClient, session_id: str, agent_id: str = "agent-test-01"):
    return client.websocket_connect(
        f"/ws/agent/{session_id}?agent_id={agent_id}"
    )


def _register(ws, agent_id: str = "agent-test-01") -> dict:
    ws.send_json(
        {
            "type": "register",
            "agent_id": agent_id,
            "agent_name": "ALPILAB-PC",
            "platform": "windows",
            "agent_version": "0.4.0",
            "capabilities": {
                "safe_test": True,
                "windows_apps": True,
                "alpilab_check": False,
                "microscope": False,
                "thermal_camera": False,
                "multimeter": False,
                "power_supply": False,
            },
            "status": "ONLINE",
        }
    )
    return ws.receive_json()


def _setup_3utools_dry_run(tmp_path) -> None:
    exe = tmp_path / "3uTools.exe"
    exe.write_text("stub", encoding="utf-8")
    configure_dispatcher({"windows_apps": True, "safe_test": True})
    local_app_registry.set_apps(
        {
            "3utools": WindowsApplicationConfig(
                app_id="3utools",
                name="3uTools",
                executable="3uTools.exe",
                executable_path=str(exe),
                enabled=True,
                dry_run=True,
            )
        }
    )
    configure_windows_app_tool(
        WindowsAppTool(registry=local_app_registry, launcher=MockProcessLauncher())
    )


# --- Parser positive ---


@pytest.mark.parametrize(
    "text",
    [
        "Apri 3uTools",
        "Aprimi 3uTools",
        "Avvia 3uTools",
        "Lancia 3uTools",
        "Puoi aprire 3uTools?",
        "Apri 3u Tools",
        "3uTools",
    ],
)
def test_parser_open_3utools_variants(parser: NaturalLanguageCommandParser, text: str) -> None:
    result = parser.parse(text)
    assert result.outcome == ParseOutcome.ACTION_COMMAND
    assert result.intent is not None
    assert result.intent.type == IntentType.OPEN_APPLICATION
    assert result.intent.target == "3utools"
    assert resolve_tool_id(result.intent) == "windows.3utools.open"


# --- Parser negative ---


@pytest.mark.parametrize(
    "text",
    [
        "Apri Borneo",
        "Apri ZXW",
        "Chiudi 3uTools",
        "Apri Chrome",
        "Apri il programma",
        "Apri quello per iPhone",
        "esegui C:\\Windows\\qualcosa.exe",
        "powershell Get-Process",
        "cmd /c dir",
    ],
)
def test_parser_rejects_unsafe_or_unsupported(
    parser: NaturalLanguageCommandParser, text: str
) -> None:
    result = parser.parse(text)
    assert result.outcome != ParseOutcome.ACTION_COMMAND
    assert result.intent is None or result.intent.type != IntentType.OPEN_APPLICATION


def test_parser_ambiguous_clarification(parser: NaturalLanguageCommandParser) -> None:
    result = parser.parse("Apri il programma")
    assert result.outcome == ParseOutcome.AMBIGUOUS
    assert result.clarification


def test_parser_invalid_command_security(parser: NaturalLanguageCommandParser) -> None:
    result = parser.parse("esegui C:\\qualcosa\\app.exe")
    assert result.outcome == ParseOutcome.INVALID_COMMAND


# --- Conversation vs command ---


@pytest.mark.parametrize(
    "text",
    [
        "Ho un iPhone 13 Pro che non si accende",
        "Come controllo PP_VDD_MAIN?",
    ],
)
def test_parser_conversation(parser: NaturalLanguageCommandParser, text: str) -> None:
    result = parser.parse(text)
    assert result.outcome == ParseOutcome.CONVERSATION


def test_parser_action_command(parser: NaturalLanguageCommandParser) -> None:
    result = parser.parse("Aprimi 3uTools")
    assert result.outcome == ParseOutcome.ACTION_COMMAND


# --- E2E pipeline ---


def test_e2e_nl_to_tool_gateway(client: TestClient, tmp_path) -> None:
    """NL parse → TOOL_EXECUTE → agent → dry-run result."""
    import asyncio

    from app.agent.gateway import agent_gateway

    _setup_3utools_dry_run(tmp_path)
    parsed = NaturalLanguageCommandParser().parse("Aprimi 3uTools")
    assert parsed.intent is not None
    tool_id = resolve_tool_id(parsed.intent)
    assert tool_id == "windows.3utools.open"

    session_id = "repair-nl-gateway"
    with _agent_connect(client, session_id) as ws_agent:
        _register(ws_agent)

        async def run() -> None:
            await agent_gateway.send_tool_execute(
                session_id, "agent-test-01", tool_id, {}
            )

        asyncio.run(run())
        cmd_msg = ws_agent.receive_json()
        local = handle_command(cmd_msg["command"], "agent-test-01")
        assert local["success"] is True
        assert local["result"]["mode"] == "dry_run"


@pytest.mark.asyncio
async def test_handle_user_message_triggers_execution(tmp_path, monkeypatch) -> None:
    from datetime import datetime, timezone

    from app.agent.payloads import AgentCapabilities, ResultEnvelope
    from app.agent.registry import RegisteredAgent
    from app.conversation import natural_language_service as nls_mod
    from app.conversation.natural_language_service import NaturalLanguageCommandService
    from app.realtime.session_manager import RealtimeSessionManager

    _setup_3utools_dry_run(tmp_path)
    rt = RealtimeSessionManager()
    rt.create_session("repair-nl-svc", seed_demo=False)
    agent_registry.register(
        RegisteredAgent(
            agent_id="agent-test-01",
            session_id="repair-nl-svc",
            agent_name="PC",
            platform="windows",
            agent_version="0.4.0",
            capabilities=AgentCapabilities(windows_apps=True, safe_test=True),
            status="ONLINE",
            connected_at=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            send_json=lambda x: None,
        )
    )

    captured: dict = {}

    async def mock_execute(session_id, agent_id, tool_id, arguments=None, **kwargs):
        captured["tool_id"] = tool_id
        return ResultEnvelope(
            request_id="req-nl",
            command_id="cmd-nl",
            agent_id=agent_id,
            tool_id=tool_id,
            success=True,
            result={"mode": "dry_run", "validated": True},
            timestamp="2026-01-01T00:00:00+00:00",
        )

    monkeypatch.setattr(
        nls_mod.tool_execution_service,
        "execute_tool",
        mock_execute,
    )
    from app.realtime import session_manager as sm_mod

    monkeypatch.setattr(sm_mod, "realtime_manager", rt)

    await NaturalLanguageCommandService().handle_user_message(
        "repair-nl-svc", "phone-01", "Aprimi 3uTools"
    )
    assert captured.get("tool_id") == "windows.3utools.open"
    session = rt.get_session("repair-nl-svc")
    assert session is not None
    assistant_msgs = [m for m in session.messages if m.role == "assistant"]
    assert len(assistant_msgs) == 1
    assert "verrebbe avviato" in assistant_msgs[0].content.lower()


@pytest.mark.asyncio
async def test_handle_user_message_failure_does_not_claim_success(
    tmp_path, monkeypatch
) -> None:
    from datetime import datetime, timezone

    from app.agent.payloads import AgentCapabilities, ResultEnvelope
    from app.agent.registry import RegisteredAgent
    from app.conversation import natural_language_service as nls_mod
    from app.conversation.natural_language_service import NaturalLanguageCommandService
    from app.realtime.session_manager import RealtimeSessionManager

    _setup_3utools_dry_run(tmp_path)
    rt = RealtimeSessionManager()
    rt.create_session("repair-nl-fail", seed_demo=False)
    agent_registry.register(
        RegisteredAgent(
            agent_id="agent-test-01",
            session_id="repair-nl-fail",
            agent_name="PC",
            platform="windows",
            agent_version="0.4.0",
            capabilities=AgentCapabilities(windows_apps=True, safe_test=True),
            status="ONLINE",
            connected_at=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            send_json=lambda x: None,
        )
    )

    async def mock_execute(session_id, agent_id, tool_id, arguments=None, **kwargs):
        return ResultEnvelope(
            request_id="req-nl-fail",
            command_id="cmd-nl-fail",
            agent_id=agent_id,
            tool_id=tool_id,
            success=False,
            result={},
            error="TOOL_DISABLED",
            timestamp="2026-01-01T00:00:00+00:00",
        )

    monkeypatch.setattr(nls_mod.tool_execution_service, "execute_tool", mock_execute)
    from app.realtime import session_manager as sm_mod

    monkeypatch.setattr(sm_mod, "realtime_manager", rt)

    await NaturalLanguageCommandService().handle_user_message(
        "repair-nl-fail", "phone-01", "Aprimi 3uTools"
    )
    session = rt.get_session("repair-nl-fail")
    assert session is not None
    assistant_msgs = [m for m in session.messages if m.role == "assistant"]
    assert len(assistant_msgs) == 1
    assert "ho aperto 3utools" not in assistant_msgs[0].content.lower()
    assert "disabilitato" in assistant_msgs[0].content.lower()


def test_e2e_conversation_no_tool_dispatch(client: TestClient, tmp_path) -> None:
    _setup_3utools_dry_run(tmp_path)
    session_id = "repair-nl-conv"

    with _agent_connect(client, session_id) as ws_agent:
        _register(ws_agent)
        with client.websocket_connect(
            f"/ws/sessions/{session_id}?device_id=phone-01&device_type=phone&device_name=Phone"
        ) as ws_phone:
            ws_phone.receive_json()
            ws_phone.send_json(
                {
                    "type": "chat_message",
                    "content": "Ho un iPhone 13 Pro che non si accende",
                    "role": "user",
                }
            )
            ws_agent.send_json({"type": "heartbeat"})
            ack = ws_agent.receive_json()
            assert ack["type"] == "heartbeat_ack"


def test_e2e_unsupported_borneo(client: TestClient, tmp_path) -> None:
    _setup_3utools_dry_run(tmp_path)
    session_id = "repair-nl-borneo"

    with _agent_connect(client, session_id) as ws_agent:
        _register(ws_agent)
        with client.websocket_connect(
            f"/ws/sessions/{session_id}?device_id=phone-01&device_type=phone&device_name=Phone"
        ) as ws_phone:
            ws_phone.receive_json()
            ws_phone.send_json(
                {"type": "chat_message", "content": "Apri Borneo", "role": "user"}
            )
            assistant_text = None
            for _ in range(8):
                msg = ws_phone.receive_json()
                if msg.get("type") == "event" and msg["event"]["event_type"] == "CHAT_MESSAGE":
                    if msg["event"]["payload"].get("role") == "assistant":
                        assistant_text = msg["event"]["payload"]["content"]
                        break
            assert assistant_text is not None
            assert "non è ancora supportato" in assistant_text.lower()
