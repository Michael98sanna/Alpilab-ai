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
from pc_agent.alpilab_check.bridge_client import (
    ALPILAB_CHECK_TIMEOUT,
    ALPILAB_CHECK_UNAUTHORIZED,
    ALPILAB_CHECK_UNAVAILABLE,
    AlpilabCheckBridgeError,
)
from pc_agent.tools.alpilab_check_handlers import configure_alpilab_check_client
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


class _FakeBridgeSuccess:
    def health(self) -> dict:
        return {"status": "ok", "protocol_version": "v1"}

    def search_products(self, query: str, limit: int = 20) -> dict:
        return {"items": [{"id": "p1", "name": "iPhone 14"}], "limit": limit}

    def get_product(self, product_id: str) -> dict:
        return {"id": product_id, "name": "iPhone Battery"}

    def search_invoices(self, query: str, limit: int = 20) -> dict:
        return {"items": [{"id": "inv1", "code": "INV-2026-01"}], "limit": limit}

    def get_invoice(self, invoice_id: str) -> dict:
        return {"id": invoice_id, "total": 120.0}


class _FakeBridgeNoResults(_FakeBridgeSuccess):
    def search_products(self, query: str, limit: int = 20) -> dict:
        return {"items": [], "limit": limit}


class _FakeBridgeError:
    def __init__(self, code: str) -> None:
        self._code = code

    def health(self) -> dict:
        raise AlpilabCheckBridgeError(self._code)

    def search_products(self, query: str, limit: int = 20) -> dict:
        raise AlpilabCheckBridgeError(self._code)

    def get_product(self, product_id: str) -> dict:
        raise AlpilabCheckBridgeError(self._code)

    def search_invoices(self, query: str, limit: int = 20) -> dict:
        raise AlpilabCheckBridgeError(self._code)

    def get_invoice(self, invoice_id: str) -> dict:
        raise AlpilabCheckBridgeError(self._code)


def _register_loopback_agent_for_nl(
    session_id: str,
    *,
    alpilab_check: bool,
) -> str:
    from datetime import datetime, timezone

    from app.agent.gateway import agent_gateway
    from app.agent.payloads import AgentCapabilities, AgentInboundMessage
    from app.agent.registry import RegisteredAgent

    agent_id = "agent-test-01"

    async def _send_json(payload: dict) -> None:
        command = payload.get("command")
        if not command:
            return
        local = handle_command(command, agent_id)
        if not local:
            return
        message = AgentInboundMessage.model_validate(local)
        if message.type == "tool_execute_result":
            await agent_gateway.handle_tool_execute_result(session_id, message)

    agent_registry.register(
        RegisteredAgent(
            agent_id=agent_id,
            session_id=session_id,
            agent_name="PC",
            platform="windows",
            agent_version="0.6.0",
            capabilities=AgentCapabilities(
                windows_apps=True,
                safe_test=True,
                alpilab_check=alpilab_check,
            ),
            status="ONLINE",
            connected_at=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            send_json=_send_json,
        )
    )
    return agent_id


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


@pytest.mark.parametrize(
    ("text", "tool_id"),
    [
        ("Cerca iPhone nel listino.", "alpilab_check.search_products"),
        ("Mostra prodotto p-001", "alpilab_check.get_product"),
        ("Cerca INV-2026 nelle fatture", "alpilab_check.search_invoices"),
        ("Mostra fattura inv-77", "alpilab_check.get_invoice"),
    ],
)
def test_parser_alpilab_check_intents(
    parser: NaturalLanguageCommandParser, text: str, tool_id: str
) -> None:
    result = parser.parse(text)
    assert result.outcome == ParseOutcome.ACTION_COMMAND
    assert result.intent is not None
    assert result.intent.type == IntentType.OPEN_TOOL
    assert resolve_tool_id(result.intent) == tool_id


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "expected_tool"),
    [
        ("Cerca iPhone nel listino.", "alpilab_check.search_products"),
        ("Mostra prodotto p-001", "alpilab_check.get_product"),
        ("Cerca INV-2026 nelle fatture", "alpilab_check.search_invoices"),
        ("Mostra fattura inv-77", "alpilab_check.get_invoice"),
    ],
)
async def test_e2e_alpilab_check_tool_selection_and_execution(
    text: str, expected_tool: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.conversation.natural_language_service import NaturalLanguageCommandService
    from app.realtime import session_manager as sm_mod
    from app.realtime.session_manager import RealtimeSessionManager

    configure_dispatcher({"windows_apps": True, "safe_test": True, "alpilab_check": True})
    configure_alpilab_check_client(_FakeBridgeSuccess())
    rt = RealtimeSessionManager()
    rt.create_session("repair-check-nl", seed_demo=False)
    _register_loopback_agent_for_nl("repair-check-nl", alpilab_check=True)

    captured: dict[str, str] = {}
    from app.agent.tool_executor import tool_execution_service as _service
    original_exec = _service.execute_tool

    async def wrapped_execute(*args, **kwargs):
        result = await original_exec(*args, **kwargs)
        captured["tool_id"] = result.tool_id or ""
        return result

    monkeypatch.setattr(_service, "execute_tool", wrapped_execute)
    monkeypatch.setattr(sm_mod, "realtime_manager", rt)

    await NaturalLanguageCommandService().handle_user_message(
        "repair-check-nl", "phone-01", text
    )
    assert captured.get("tool_id") == expected_tool
    session = rt.get_session("repair-check-nl")
    assert session is not None
    assistant_msgs = [m for m in session.messages if m.role == "assistant"]
    assert assistant_msgs
    assert "invent" not in assistant_msgs[-1].content.lower()


@pytest.mark.asyncio
async def test_e2e_alpilab_check_capability_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.conversation.natural_language_service import NaturalLanguageCommandService
    from app.realtime import session_manager as sm_mod
    from app.realtime.session_manager import RealtimeSessionManager

    configure_dispatcher({"windows_apps": True, "safe_test": True, "alpilab_check": False})
    rt = RealtimeSessionManager()
    rt.create_session("repair-check-cap-nl", seed_demo=False)
    _register_loopback_agent_for_nl("repair-check-cap-nl", alpilab_check=False)
    monkeypatch.setattr(sm_mod, "realtime_manager", rt)
    await NaturalLanguageCommandService().handle_user_message(
        "repair-check-cap-nl", "phone-01", "Cerca iPhone nel listino."
    )
    session = rt.get_session("repair-check-cap-nl")
    assistant_msgs = [m for m in session.messages if m.role == "assistant"]
    assert assistant_msgs
    assert "capability" in assistant_msgs[-1].content.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("err_code", [ALPILAB_CHECK_UNAVAILABLE, ALPILAB_CHECK_TIMEOUT, ALPILAB_CHECK_UNAUTHORIZED])
async def test_e2e_alpilab_check_bridge_error_propagation(
    err_code: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.conversation.natural_language_service import NaturalLanguageCommandService
    from app.realtime import session_manager as sm_mod
    from app.realtime.session_manager import RealtimeSessionManager

    configure_dispatcher({"windows_apps": True, "safe_test": True, "alpilab_check": True})
    configure_alpilab_check_client(_FakeBridgeError(err_code))
    rt = RealtimeSessionManager()
    rt.create_session("repair-check-err-nl", seed_demo=False)
    _register_loopback_agent_for_nl("repair-check-err-nl", alpilab_check=True)
    monkeypatch.setattr(sm_mod, "realtime_manager", rt)
    await NaturalLanguageCommandService().handle_user_message(
        "repair-check-err-nl", "phone-01", "Cerca iPhone nel listino."
    )
    session = rt.get_session("repair-check-err-nl")
    assistant_msgs = [m for m in session.messages if m.role == "assistant"]
    assert assistant_msgs
    msg = assistant_msgs[-1].content.lower()
    assert "alpilab check" in msg or "autorizzato" in msg
    assert err_code.lower() not in msg


@pytest.mark.asyncio
async def test_e2e_alpilab_check_no_results_no_invention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.conversation.natural_language_service import NaturalLanguageCommandService
    from app.realtime import session_manager as sm_mod
    from app.realtime.session_manager import RealtimeSessionManager

    configure_dispatcher({"windows_apps": True, "safe_test": True, "alpilab_check": True})
    configure_alpilab_check_client(_FakeBridgeNoResults())
    rt = RealtimeSessionManager()
    rt.create_session("repair-check-empty-nl", seed_demo=False)
    _register_loopback_agent_for_nl("repair-check-empty-nl", alpilab_check=True)
    monkeypatch.setattr(sm_mod, "realtime_manager", rt)
    await NaturalLanguageCommandService().handle_user_message(
        "repair-check-empty-nl", "phone-01", "Cerca iPhone nel listino."
    )
    session = rt.get_session("repair-check-empty-nl")
    assistant_msgs = [m for m in session.messages if m.role == "assistant"]
    assert assistant_msgs
    msg = assistant_msgs[-1].content.lower()
    assert "non ho trovato prodotti" in msg
    assert "iphone 15" not in msg


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


def test_parser_open_borneo(parser: NaturalLanguageCommandParser) -> None:
    result = parser.parse("Apri Borneo")
    assert result.outcome == ParseOutcome.ACTION_COMMAND
    assert result.intent is not None
    assert result.intent.target == "borneo"
    assert resolve_tool_id(result.intent) == "windows.borneo.open"


@pytest.mark.asyncio
async def test_handle_user_message_opens_borneo(tmp_path, monkeypatch) -> None:
    from datetime import datetime, timezone

    from app.agent.payloads import AgentCapabilities, ResultEnvelope
    from app.agent.registry import RegisteredAgent
    from app.conversation import natural_language_service as nls_mod
    from app.conversation.natural_language_service import NaturalLanguageCommandService
    from app.realtime.session_manager import RealtimeSessionManager

    shortcut = tmp_path / "Borneo Schematics.exe"
    shortcut.write_bytes(b"MZ")
    configure_dispatcher({"windows_apps": True, "safe_test": True})
    local_app_registry.set_apps(
        {
            "borneo": WindowsApplicationConfig(
                app_id="borneo",
                name="Borneo",
                executable="Borneo Schematics.exe",
                executable_path=str(shortcut),
                enabled=True,
                dry_run=True,
            )
        }
    )
    configure_windows_app_tool(
        WindowsAppTool(registry=local_app_registry, launcher=MockProcessLauncher())
    )

    rt = RealtimeSessionManager()
    rt.create_session("repair-nl-borneo", seed_demo=False)
    agent_registry.register(
        RegisteredAgent(
            agent_id="agent-test-01",
            session_id="repair-nl-borneo",
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
            request_id="req-borneo",
            command_id="cmd-borneo",
            agent_id=agent_id,
            tool_id=tool_id,
            success=True,
            result={"mode": "dry_run", "validated": True},
            timestamp="2026-01-01T00:00:00+00:00",
        )

    monkeypatch.setattr(nls_mod.tool_execution_service, "execute_tool", mock_execute)
    from app.realtime import session_manager as sm_mod

    monkeypatch.setattr(sm_mod, "realtime_manager", rt)

    await NaturalLanguageCommandService().handle_user_message(
        "repair-nl-borneo", "phone-01", "Apri Borneo"
    )
    assert captured.get("tool_id") == "windows.borneo.open"
    session = rt.get_session("repair-nl-borneo")
    assert session is not None
    assistant_msgs = [m for m in session.messages if m.role == "assistant"]
    assert len(assistant_msgs) == 1
    assert "borneo" in assistant_msgs[0].content.lower()


def test_e2e_unsupported_zxw(client: TestClient, tmp_path) -> None:
    _setup_3utools_dry_run(tmp_path)
    session_id = "repair-nl-zxw"

    with _agent_connect(client, session_id) as ws_agent:
        _register(ws_agent)
        with client.websocket_connect(
            f"/ws/sessions/{session_id}?device_id=phone-01&device_type=phone&device_name=Phone"
        ) as ws_phone:
            ws_phone.receive_json()
            ws_phone.send_json(
                {"type": "chat_message", "content": "Apri ZXW", "role": "user"}
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
