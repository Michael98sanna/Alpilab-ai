"""PC Agent WebSocket and registry tests."""

import json

import pytest
from fastapi.testclient import TestClient

from app.agent.registry import agent_registry
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    agent_registry.clear()
    from app.realtime import session_manager as sm

    sm.realtime_manager._sessions.clear()
    sm.realtime_manager._ws_connections.clear()


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
            "agent_version": "0.1.0",
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


def test_agent_registration(client: TestClient) -> None:
    session_id = "repair-agent-001"
    with _agent_connect(client, session_id) as ws:
        resp = _register(ws)
        assert resp["type"] == "registered"
        assert resp["message"] == "REGISTERED"
        agents = agent_registry.list_agents(session_id)
        assert len(agents) == 1
        assert agents[0].agent_id == "agent-test-01"
        assert agents[0].status == "ONLINE"


def test_duplicate_registration_replaces(client: TestClient) -> None:
    session_id = "repair-agent-dup"
    with _agent_connect(client, session_id, "agent-dup") as ws1:
        _register(ws1, "agent-dup")
    with _agent_connect(client, session_id, "agent-dup") as ws2:
        resp = _register(ws2, "agent-dup")
        assert resp["type"] == "registered"
        assert agent_registry.count(session_id) == 1


def test_agent_heartbeat(client: TestClient) -> None:
    session_id = "repair-agent-hb"
    with _agent_connect(client, session_id) as ws:
        _register(ws)
        ws.send_json({"type": "heartbeat"})
        ack = ws.receive_json()
        assert ack["type"] == "heartbeat_ack"
        agent = agent_registry.get(session_id, "agent-test-01")
        assert agent is not None
        assert agent.status == "ONLINE"


def test_agent_unregister_on_disconnect(client: TestClient) -> None:
    session_id = "repair-agent-disc"
    ws_ctx = _agent_connect(client, session_id)
    ws = ws_ctx.__enter__()
    _register(ws)
    ws_ctx.__exit__(None, None, None)
    assert agent_registry.count(session_id) == 0


def test_agents_status_endpoint(client: TestClient) -> None:
    session_id = "repair-agent-status"
    with _agent_connect(client, session_id) as ws:
        _register(ws)
        response = client.get(f"/api/v1/agents/status?session_id={session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["agents_online"] == 1
        assert data["agents"][0]["agent_id"] == "agent-test-01"


def test_mobile_seeds_empty_session_after_agent(client: TestClient) -> None:
    """PC Agent may create an empty session before mobile connects with seed_demo."""
    session_id = "repair-agent-seed"
    with _agent_connect(client, session_id) as ws:
        _register(ws)

    with client.websocket_connect(
        f"/ws/sessions/{session_id}"
        "?device_id=phone-01&device_type=phone&device_name=Phone&seed_demo=true"
    ) as ws_phone:
        snap = ws_phone.receive_json()
        assert snap["type"] == "snapshot"
        session = snap["payload"]["session"]
        assert session["device"] == "iPhone 13 Pro"
        assert session["issue"] == "No Power"
        assert len(snap["payload"]["diagnostic_state"]) >= 1


def test_agent_test_command(client: TestClient) -> None:
    session_id = "repair-agent-test"
    with _agent_connect(client, session_id) as ws:
        _register(ws)
        response = client.post(
            f"/api/v1/sessions/{session_id}/agents/agent-test-01/test"
        )
        assert response.status_code == 200
        cmd = ws.receive_json()
        assert cmd["type"] == "command"
        assert cmd["command"]["type"] == "AGENT_TEST"
        ws.send_json(
            {
                "type": "agent_test_result",
                "request_id": cmd["command"]["request_id"],
                "command_id": cmd["command"]["command_id"],
                "agent_id": "agent-test-01",
                "success": True,
                "result": {"message": "pong"},
                "timestamp": "2026-01-01T00:00:00+00:00",
            }
        )


def test_unknown_command_rejected_by_agent(client: TestClient) -> None:
    from pc_agent.commands import handle_command

    result = handle_command(
        {"type": "OPEN_APPLICATION", "request_id": "r1", "command_id": "c1"},
        "agent-test-01",
    )
    assert result is not None
    assert result["success"] is False
    assert result["error"] == "COMMAND_NOT_ALLOWED"


def test_malformed_register_rejected(client: TestClient) -> None:
    session_id = "repair-agent-bad"
    with _agent_connect(client, session_id) as ws:
        ws.send_json({"type": "heartbeat"})
        err = ws.receive_json()
        assert err["type"] == "error"


def _receive_event(ws, event_type: str) -> dict:
    while True:
        msg = ws.receive_json()
        if msg.get("type") == "event" and msg["event"]["event_type"] == event_type:
            return msg


def test_agent_broadcast_to_session_client(client: TestClient) -> None:
    session_id = "repair-agent-broadcast"
    with client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id=phone-01&device_type=phone&device_name=Phone"
    ) as ws_phone:
        ws_phone.receive_json()  # snapshot
        with _agent_connect(client, session_id) as ws_agent:
            _register(ws_agent)
            evt = _receive_event(ws_phone, "AGENT_CONNECTED")
            assert evt["event"]["payload"]["online"] is True


def test_agent_disconnect_broadcast(client: TestClient) -> None:
    session_id = "repair-agent-offline"
    with client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id=phone-01&device_type=phone&device_name=Phone"
    ) as ws_phone:
        ws_phone.receive_json()
        ws_ctx = _agent_connect(client, session_id)
        ws_agent = ws_ctx.__enter__()
        _register(ws_agent)
        _receive_event(ws_phone, "AGENT_CONNECTED")
        ws_ctx.__exit__(None, None, None)
        evt = _receive_event(ws_phone, "AGENT_DISCONNECTED")
        assert evt["event"]["payload"]["online"] is False


def test_snapshot_includes_pc_agent(client: TestClient) -> None:
    session_id = "repair-agent-snap"
    with client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id=pc-01&device_type=pc&device_name=PC"
    ) as ws_pc:
        snap = ws_pc.receive_json()
        assert snap["type"] == "snapshot"
        assert snap["payload"]["pc_agent"] is None
        with _agent_connect(client, session_id) as ws_agent:
            _register(ws_agent)
            _receive_event(ws_pc, "AGENT_CONNECTED")
            with client.websocket_connect(
                f"/ws/sessions/{session_id}?device_id=pc-02&device_type=pc&device_name=PC2"
            ) as ws_pc2:
                snap2 = ws_pc2.receive_json()
                assert snap2["payload"]["pc_agent"] is not None
                assert snap2["payload"]["pc_agent"]["online"] is True
