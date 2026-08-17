"""Tool execution pipeline tests — V0.2."""

import pytest
from fastapi.testclient import TestClient

from app.agent.execution_store import tool_execution_store
from app.agent.registry import agent_registry
from app.security.tool_authorization import authorize_tool_execution
from app.agent.payloads import AgentCapabilities
from app.schemas.enums import ActionRiskLevel
from app.tools.executable import SAFE_TEST_TOOL, validate_tool_arguments
from app.tools.registry import default_tool_registry
from app.main import app
from pc_agent.commands import handle_command
from pc_agent.tools.dispatcher import LocalToolDispatcher


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    agent_registry.clear()
    tool_execution_store.clear()
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
            "agent_version": "0.2.0",
            "capabilities": {
                "safe_test": True,
                "windows_apps": False,
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


# --- Registry ---


def test_tool_registration() -> None:
    spec = default_tool_registry.get_executable("demo.safe_test")
    assert spec is not None
    assert spec.tool_id == "demo.safe_test"
    assert spec.enabled is True


def test_tool_lookup() -> None:
    assert default_tool_registry.resolve_executable("demo.safe_test") is not None


def test_unknown_tool() -> None:
    assert default_tool_registry.get_executable("unknown.tool") is None


def test_disabled_tool() -> None:
    default_tool_registry.register_executable(
        SAFE_TEST_TOOL.model_copy(update={"tool_id": "demo.disabled", "enabled": False})
    )
    assert default_tool_registry.is_enabled("demo.disabled") is False
    assert default_tool_registry.resolve_executable("demo.disabled") is None


def test_list_tools_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    tools = response.json()["tools"]
    assert any(t["tool_id"] == "demo.safe_test" for t in tools)


# --- Authorization ---


def test_authorization_low_safe_test() -> None:
    auth = authorize_tool_execution(SAFE_TEST_TOOL, AgentCapabilities(safe_test=True))
    assert auth.allowed is True


def test_authorization_denied_high_risk() -> None:
    high_risk = SAFE_TEST_TOOL.model_copy(
        update={"tool_id": "demo.high", "risk_level": ActionRiskLevel.DANGEROUS}
    )
    auth = authorize_tool_execution(high_risk, AgentCapabilities(safe_test=True))
    assert auth.allowed is False
    assert auth.metadata.get("error") == "AUTHORIZATION_DENIED"


def test_capability_missing() -> None:
    auth = authorize_tool_execution(
        SAFE_TEST_TOOL,
        AgentCapabilities(safe_test=False),
    )
    assert auth.allowed is False
    assert auth.metadata.get("error") == "CAPABILITY_MISSING"


# --- Argument validation ---


def test_invalid_arguments() -> None:
    assert validate_tool_arguments(SAFE_TEST_TOOL, {"foo": "bar"}) == "INVALID_ARGUMENTS"


def test_valid_empty_arguments() -> None:
    assert validate_tool_arguments(SAFE_TEST_TOOL, {}) is None


# --- PC Agent local ---


def test_pc_agent_safe_test_local() -> None:
    result = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-safe-1",
            "command_id": "cmd-1",
            "payload": {"tool_id": "demo.safe_test", "arguments": {}},
        },
        "agent-local",
    )
    assert result is not None
    assert result["type"] == "tool_execute_result"
    assert result["success"] is True
    assert result["result"]["message"] == "Alpilab PC Agent tool execution works"


def test_pc_agent_unknown_tool_rejection() -> None:
    result = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-unk",
            "command_id": "cmd-2",
            "payload": {"tool_id": "unknown.tool", "arguments": {}},
        },
        "agent-local",
    )
    assert result is not None
    assert result["success"] is False
    assert result["error"] == "TOOL_NOT_FOUND"


def test_pc_agent_invalid_arguments_rejection() -> None:
    result = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-bad-args",
            "command_id": "cmd-3",
            "payload": {"tool_id": "demo.safe_test", "arguments": {"foo": "bar"}},
        },
        "agent-local",
    )
    assert result is not None
    assert result["success"] is False
    assert result["error"] == "INVALID_ARGUMENTS"


def test_pc_agent_unknown_command_type() -> None:
    result = handle_command(
        {"type": "RUN_SHELL", "request_id": "req-shell"},
        "agent-local",
    )
    assert result is not None
    assert result["success"] is False
    assert result["error"] == "COMMAND_NOT_ALLOWED"


def test_pc_agent_duplicate_command_idempotent() -> None:
    cmd = {
        "type": "TOOL_EXECUTE",
        "request_id": "req-dup",
        "command_id": "cmd-dup",
        "payload": {"tool_id": "demo.safe_test", "arguments": {}},
    }
    first = handle_command(cmd, "agent-local")
    second = handle_command(cmd, "agent-local")
    assert first == second


def test_pc_agent_capability_rejection() -> None:
    dispatcher = LocalToolDispatcher(capabilities={"safe_test": False})
    result = dispatcher.dispatch(
        "demo.safe_test",
        {},
        request_id="req-cap",
        command_id="cmd-cap",
        agent_id="agent-local",
    )
    assert result["success"] is False
    assert result["error"] == "CAPABILITY_MISSING"


# --- E2E via WebSocket + gateway ---


def _run_tool_pipeline(client: TestClient, ws_agent, session_id: str, agent_id: str = "agent-test-01") -> dict:
    """Send TOOL_EXECUTE via gateway, drive agent WS, return local result."""
    import asyncio

    from app.agent.gateway import agent_gateway

    async def send() -> None:
        await agent_gateway.send_tool_execute(
            session_id,
            agent_id,
            "demo.safe_test",
            {},
        )

    asyncio.run(send())
    cmd_msg = ws_agent.receive_json()
    assert cmd_msg["type"] == "command"
    assert cmd_msg["command"]["type"] == "TOOL_EXECUTE"
    assert cmd_msg["command"]["payload"]["tool_id"] == "demo.safe_test"
    local = handle_command(cmd_msg["command"], agent_id)
    ws_agent.send_json(local)
    return local


def test_safe_test_execution_e2e(client: TestClient) -> None:
    """Gateway → agent WS → local handler → result store."""
    session_id = "repair-tool-e2e"
    with _agent_connect(client, session_id) as ws_agent:
        _register(ws_agent)
        local = _run_tool_pipeline(client, ws_agent, session_id)
        assert local["success"] is True
        assert local["result"]["message"] == "Alpilab PC Agent tool execution works"
        assert len(tool_execution_store._completed) == 1


def test_safe_test_real_agent_roundtrip(client: TestClient) -> None:
    """Full pipeline with smartphone receiving TOOL_EXECUTE_RESULT."""
    session_id = "repair-tool-rt"
    with _agent_connect(client, session_id) as ws_agent:
        _register(ws_agent)
        with client.websocket_connect(
            f"/ws/sessions/{session_id}?device_id=phone-01&device_type=phone&device_name=Phone"
        ) as ws_phone:
            ws_phone.receive_json()  # snapshot

            _run_tool_pipeline(client, ws_agent, session_id)

            event_types: set[str] = set()
            result_payload = None
            for _ in range(3):
                msg = ws_phone.receive_json()
                if msg.get("type") != "event":
                    continue
                et = msg["event"]["event_type"]
                event_types.add(et)
                if et == "TOOL_EXECUTE_RESULT":
                    result_payload = msg["event"]["payload"]

            assert "TOOL_EXECUTION_STARTED" in event_types
            assert "TOOL_EXECUTION_COMPLETED" in event_types
            assert "TOOL_EXECUTE_RESULT" in event_types
            assert result_payload is not None
            assert result_payload["success"] is True
            assert (
                result_payload["result"]["message"]
                == "Alpilab PC Agent tool execution works"
            )


def test_tool_execution_timeout(client: TestClient) -> None:
    import asyncio

    from app.agent.tool_executor import ToolExecutionError, ToolExecutionService

    session_id = "repair-tool-timeout"
    service = ToolExecutionService()
    with _agent_connect(client, session_id) as ws:
        _register(ws)

        async def run() -> None:
            try:
                await service.execute_tool(
                    session_id,
                    "agent-test-01",
                    "demo.safe_test",
                    {},
                    timeout_sec=0.05,
                )
            except ToolExecutionError as exc:
                assert exc.error_code == "TOOL_EXECUTION_TIMEOUT"
            else:
                raise AssertionError("expected timeout")

        asyncio.run(run())


def test_unknown_tool_via_service(client: TestClient) -> None:
    import asyncio

    from app.agent.tool_executor import ToolExecutionError, tool_execution_service

    session_id = "repair-tool-unknown"
    with _agent_connect(client, session_id) as ws:
        _register(ws)

        async def run() -> None:
            try:
                await tool_execution_service.execute_tool(
                    session_id,
                    "agent-test-01",
                    "unknown.tool",
                    {},
                )
            except ToolExecutionError as exc:
                assert exc.error_code == "TOOL_NOT_FOUND"
            else:
                raise AssertionError("expected TOOL_NOT_FOUND")

        asyncio.run(run())


def test_tool_execute_envelope(client: TestClient) -> None:
    import asyncio

    from app.agent.gateway import agent_gateway

    session_id = "repair-tool-env"
    with _agent_connect(client, session_id) as ws:
        _register(ws)

        async def run() -> None:
            command = await agent_gateway.send_tool_execute(
                session_id,
                "agent-test-01",
                "demo.safe_test",
                {},
            )
            assert command.type == "TOOL_EXECUTE"
            assert command.source == "alpilab_ai"
            assert command.target == "agent-test-01"
            assert command.payload["tool_id"] == "demo.safe_test"
            assert command.payload["arguments"] == {}

        asyncio.run(run())
        cmd_msg = ws.receive_json()
        assert cmd_msg["command"]["request_id"]


def test_repair_session_event_log(client: TestClient) -> None:
    from app.realtime.session_manager import realtime_manager

    session_id = "repair-tool-audit"
    with _agent_connect(client, session_id) as ws_agent:
        _register(ws_agent)
        _run_tool_pipeline(client, ws_agent, session_id)
        log = realtime_manager.events_for_session(session_id)
        types = {e.event_type.value for e in log}
        assert "TOOL_EXECUTION_STARTED" in types
        assert "TOOL_EXECUTION_COMPLETED" in types
        assert "TOOL_EXECUTE_RESULT" in types


def test_pc_agent_malformed_tool_execute() -> None:
    result = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-malformed",
            "command_id": "cmd-malformed",
            "payload": {},
        },
        "agent-local",
    )
    assert result is not None
    assert result["success"] is False
    assert result["error"] == "TOOL_NOT_FOUND"


def test_duplicate_execution_idempotent(client: TestClient) -> None:
    from app.agent.payloads import ResultEnvelope

    req_id = "req-idem-1"
    tool_execution_store.complete(
        ResultEnvelope(
            request_id=req_id,
            command_id="cmd-idem",
            agent_id="agent-test-01",
            tool_id="demo.safe_test",
            success=True,
            result={"status": "ok", "message": "cached"},
            timestamp="2026-01-01T00:00:00+00:00",
        )
    )
    cached = tool_execution_store.get_completed(req_id)
    assert cached is not None
    assert cached.result["message"] == "cached"
    second = tool_execution_store.get_completed(req_id)
    assert second is cached


def test_agent_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sessions/repair-none/agents/missing-agent/tools/demo.safe_test/execute"
    )
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["error"] == "AGENT_NOT_FOUND"
