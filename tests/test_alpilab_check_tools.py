"""Milestone 2 tests for Alpilab Check tools via PC Agent path."""

from __future__ import annotations

import asyncio
import os

import pytest
from fastapi.testclient import TestClient

from app.agent.registry import agent_registry
from app.agent.tool_executor import ToolExecutionError, tool_execution_service
from app.main import app
from app.realtime.session_manager import realtime_manager
from app.tools.registry import default_tool_registry
from pc_agent.alpilab_check.bridge_client import (
    ALPILAB_CHECK_PROTOCOL_MISMATCH,
    ALPILAB_CHECK_TIMEOUT,
    ALPILAB_CHECK_UNAUTHORIZED,
    ALPILAB_CHECK_UNAVAILABLE,
    AlpilabCheckBridgeError,
)
from pc_agent.commands import configure_dispatcher
from pc_agent.commands import handle_command
from pc_agent.tools.alpilab_check_handlers import configure_alpilab_check_client


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPILAB_CHECK_BRIDGE_SECRET", "test-secret")
    agent_registry.clear()
    from app.agent.execution_store import tool_execution_store

    tool_execution_store.clear()
    realtime_manager._sessions.clear()
    realtime_manager._ws_connections.clear()
    realtime_manager._event_log.clear()
    configure_alpilab_check_client(None)
    yield
    configure_alpilab_check_client(None)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class _FakeBridgeSuccess:
    def health(self) -> dict:
        return {"status": "ok", "protocol_version": "v1"}

    def search_products(self, query: str, limit: int = 20) -> dict:
        return {"items": [{"id": "p1", "name": query}], "limit": limit}

    def get_product(self, product_id: str) -> dict:
        return {"id": product_id, "name": "Battery iPhone"}

    def search_invoices(self, query: str, limit: int = 20) -> dict:
        return {"items": [{"id": "i1", "code": query}], "limit": limit}

    def get_invoice(self, invoice_id: str) -> dict:
        return {"id": invoice_id, "total": 149.99}


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


def _register(ws, *, alpilab_check: bool = True, agent_id: str = "agent-check-01") -> None:
    ws.send_json(
        {
            "type": "register",
            "agent_id": agent_id,
            "agent_name": "ALPILAB-PC",
            "platform": "windows",
            "agent_version": "0.3.0",
            "capabilities": {
                "safe_test": True,
                "windows_apps": True,
                "alpilab_check": alpilab_check,
                "microscope": False,
                "thermal_camera": False,
                "multimeter": False,
                "power_supply": False,
            },
            "status": "ONLINE",
        }
    )
    ack = ws.receive_json()
    assert ack["type"] == "registered"


def _run_pipeline(client: TestClient, ws_agent, tool_id: str, arguments: dict, session_id: str) -> dict:
    from app.agent.gateway import agent_gateway

    async def send() -> None:
        await agent_gateway.send_tool_execute(session_id, "agent-check-01", tool_id, arguments)

    asyncio.run(send())
    cmd_msg = ws_agent.receive_json()
    local = handle_command(cmd_msg["command"], "agent-check-01")
    ws_agent.send_json(local)
    return local


# 1-4 success cases
@pytest.mark.parametrize(
    ("tool_id", "arguments", "expected_key"),
    [
        ("alpilab_check.search_products", {"query": "iphone", "limit": 5}, "items"),
        ("alpilab_check.get_product", {"product_id": "p-001"}, "id"),
        ("alpilab_check.search_invoices", {"query": "INV-2026", "limit": 3}, "items"),
        ("alpilab_check.get_invoice", {"invoice_id": "inv-77"}, "id"),
    ],
)
def test_alpilab_check_tool_success(
    client: TestClient,
    tool_id: str,
    arguments: dict,
    expected_key: str,
) -> None:
    configure_dispatcher({"safe_test": True, "windows_apps": True, "alpilab_check": True})
    configure_alpilab_check_client(_FakeBridgeSuccess())
    session_id = "repair-check-success"
    with client.websocket_connect(f"/ws/agent/{session_id}?agent_id=agent-check-01") as ws_agent:
        _register(ws_agent, alpilab_check=True)
        local = _run_pipeline(client, ws_agent, tool_id, arguments, session_id)
        assert local["success"] is True
        assert expected_key in local["result"]


# 5-8 bridge error mapping
@pytest.mark.parametrize(
    ("err_code", "tool_id", "arguments"),
    [
        (ALPILAB_CHECK_UNAVAILABLE, "alpilab_check.search_products", {"query": "x", "limit": 1}),
        (ALPILAB_CHECK_TIMEOUT, "alpilab_check.get_product", {"product_id": "p-1"}),
        (ALPILAB_CHECK_PROTOCOL_MISMATCH, "alpilab_check.search_invoices", {"query": "i", "limit": 1}),
        (ALPILAB_CHECK_UNAUTHORIZED, "alpilab_check.get_invoice", {"invoice_id": "i-1"}),
    ],
)
def test_alpilab_check_bridge_errors_propagated(
    client: TestClient,
    err_code: str,
    tool_id: str,
    arguments: dict,
) -> None:
    configure_dispatcher({"safe_test": True, "windows_apps": True, "alpilab_check": True})
    configure_alpilab_check_client(_FakeBridgeError(err_code))
    session_id = "repair-check-errors"
    with client.websocket_connect(f"/ws/agent/{session_id}?agent_id=agent-check-01") as ws_agent:
        _register(ws_agent, alpilab_check=True)
        local = _run_pipeline(client, ws_agent, tool_id, arguments, session_id)
        assert local["success"] is False
        assert local["error"] == err_code


# 9 capability missing -> authorization denied
def test_capability_missing_authorization_denied(client: TestClient) -> None:
    configure_dispatcher({"safe_test": True, "windows_apps": True, "alpilab_check": False})
    session_id = "repair-check-cap"
    with client.websocket_connect(f"/ws/agent/{session_id}?agent_id=agent-check-01") as ws_agent:
        _register(ws_agent, alpilab_check=False)

        async def run() -> None:
            with pytest.raises(ToolExecutionError) as exc:
                await tool_execution_service.execute_tool(
                    session_id,
                    "agent-check-01",
                    "alpilab_check.search_products",
                    {"query": "iphone", "limit": 5},
                )
            assert exc.value.error_code == "CAPABILITY_MISSING"

        asyncio.run(run())


# 10 invalid arguments rejected
def test_alpilab_check_invalid_arguments_rejected(client: TestClient) -> None:
    configure_dispatcher({"safe_test": True, "windows_apps": True, "alpilab_check": True})
    configure_alpilab_check_client(_FakeBridgeSuccess())
    session_id = "repair-check-invalid-args"
    with client.websocket_connect(f"/ws/agent/{session_id}?agent_id=agent-check-01") as ws_agent:
        _register(ws_agent, alpilab_check=True)

        async def run() -> None:
            with pytest.raises(ToolExecutionError) as exc:
                await tool_execution_service.execute_tool(
                    session_id,
                    "agent-check-01",
                    "alpilab_check.search_products",
                    {"query": "iphone", "unexpected": "x"},
                )
            assert exc.value.error_code == "INVALID_ARGUMENTS"

        asyncio.run(run())


# 11 secret not present in logs/events
def test_secret_not_in_events_or_result_payload(client: TestClient) -> None:
    secret = os.environ["ALPILAB_CHECK_BRIDGE_SECRET"]
    configure_dispatcher({"safe_test": True, "windows_apps": True, "alpilab_check": True})
    configure_alpilab_check_client(_FakeBridgeSuccess())
    session_id = "repair-check-secret"
    with client.websocket_connect(f"/ws/agent/{session_id}?agent_id=agent-check-01") as ws_agent:
        _register(ws_agent, alpilab_check=True)
        with client.websocket_connect(
            f"/ws/sessions/{session_id}?device_id=phone-01&device_type=phone&device_name=Phone"
        ) as ws_phone:
            ws_phone.receive_json()  # snapshot
            local = _run_pipeline(
                client,
                ws_agent,
                "alpilab_check.search_products",
                {"query": "iphone", "limit": 1},
                session_id,
            )
            assert secret not in str(local)
            for _ in range(4):
                msg = ws_phone.receive_json()
                assert secret not in str(msg)
                if msg.get("type") == "event" and msg["event"]["event_type"] == "TOOL_EXECUTE_RESULT":
                    break


# 12 regression windows.3utools.open still registered
def test_windows_3utools_tool_still_registered() -> None:
    spec = default_tool_registry.get_executable("windows.3utools.open")
    assert spec is not None
    assert spec.required_capabilities == ["windows_apps"]


# 13 regression existing PC Agent safe tool still works
def test_pc_agent_safe_test_regression() -> None:
    result = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-safe-reg",
            "command_id": "cmd-safe-reg",
            "payload": {"tool_id": "demo.safe_test", "arguments": {}},
        },
        "agent-local",
    )
    assert result is not None
    assert result["success"] is True
