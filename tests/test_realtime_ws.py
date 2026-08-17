"""WebSocket and realtime session tests."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.realtime.session_manager import RealtimeSessionManager


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def manager() -> RealtimeSessionManager:
    from app.realtime import session_manager as sm

    sm.realtime_manager._sessions.clear()
    sm.realtime_manager._ws_connections.clear()
    sm.realtime_manager._event_log.clear()
    sm.realtime_manager._subscribers.clear()
    return sm.realtime_manager


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "alpilab-ai"


def test_create_session(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sessions",
        json={"session_id": "repair-001", "seed_demo": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "repair-001"
    assert data["device"] == "iPhone 13 Pro"


def test_realtime_status(client: TestClient) -> None:
    client.post("/api/v1/sessions", json={"session_id": "repair-status"})
    response = client.get("/api/v1/realtime/status")
    assert response.status_code == 200
    assert response.json()["active_sessions"] >= 1


def test_websocket_connect_and_snapshot(client: TestClient) -> None:
    with client.websocket_connect(
        "/ws/sessions/repair-ws-001"
        "?device_id=pc-01&device_type=pc&device_name=Lab-PC&seed_demo=true"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "snapshot"
        assert msg["payload"]["session"]["id"] == "repair-ws-001"
        assert len(msg["payload"]["conversation"]) >= 1


def test_websocket_chat_broadcast(client: TestClient) -> None:
    session_id = "repair-chat-001"
    client.post("/api/v1/sessions", json={"session_id": session_id, "seed_demo": True})

    with client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id=pc-01&device_type=pc&device_name=PC"
    ) as ws_pc:
        ws_pc.receive_json()  # snapshot

        with client.websocket_connect(
            f"/ws/sessions/{session_id}?device_id=phone-01&device_type=phone&device_name=Phone"
        ) as ws_phone:
            ws_phone.receive_json()  # snapshot phone
            connected = ws_pc.receive_json()
            assert connected["type"] == "event"
            assert connected["event"]["event_type"] == "DEVICE_CONNECTED"

            ws_phone.send_json(
                {"type": "chat_message", "content": "Ciao Alpilab", "role": "user"}
            )
            chat_phone = ws_phone.receive_json()
            assert chat_phone["type"] == "event"
            assert chat_phone["event"]["event_type"] == "CHAT_MESSAGE"
            assert chat_phone["event"]["payload"]["content"] == "Ciao Alpilab"
            ws_phone.receive_json()  # ack

            chat_pc = ws_pc.receive_json()
            assert chat_pc["type"] == "event"
            assert chat_pc["event"]["event_type"] == "CHAT_MESSAGE"
            assert chat_pc["event"]["payload"]["content"] == "Ciao Alpilab"


def test_websocket_device_disconnect(client: TestClient) -> None:
    session_id = "repair-disc-001"
    with client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id=pc-01&device_type=pc&device_name=PC"
    ) as ws_pc:
        ws_pc.receive_json()
        with client.websocket_connect(
            f"/ws/sessions/{session_id}?device_id=phone-01&device_type=phone&device_name=Phone"
        ) as ws_phone:
            ws_phone.receive_json()
            ws_pc.receive_json()  # DEVICE_CONNECTED
        disconnected = ws_pc.receive_json()
        assert disconnected["event"]["event_type"] == "DEVICE_DISCONNECTED"


def test_websocket_heartbeat(client: TestClient, manager: RealtimeSessionManager) -> None:
    session_id = "repair-hb-001"
    with client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id=pc-01&device_type=pc&device_name=PC"
    ) as ws:
        ws.receive_json()
        ws.send_json({"type": "heartbeat"})
        ws.receive_json()  # ack
        session = manager.get_session(session_id)
        assert session is not None
        assert session.devices["pc-01"].online is True


def test_websocket_invalid_device_type(client: TestClient) -> None:
    with client.websocket_connect(
        "/ws/sessions/repair-invalid?device_id=d1&device_type=watch&device_name=X"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"


def test_websocket_invalid_chat_payload(client: TestClient) -> None:
    with client.websocket_connect(
        "/ws/sessions/repair-bad-msg?device_id=pc-01&device_type=pc&device_name=PC"
    ) as ws:
        ws.receive_json()
        ws.send_json({"type": "chat_message", "content": "   "})
        err = ws.receive_json()
        assert err["type"] == "error"


def test_session_event_ordering(client: TestClient, manager: RealtimeSessionManager) -> None:
    session_id = "repair-order-001"
    with client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id=pc-01&device_type=pc&device_name=PC"
    ) as ws:
        ws.receive_json()
        ws.send_json({"type": "chat_message", "content": "Primo", "role": "user"})
        ws.receive_json()
        ws.receive_json()
        ws.send_json({"type": "chat_message", "content": "Secondo", "role": "user"})
        ws.receive_json()
        ws.receive_json()
    events = manager.events_for_session(session_id)
    chat_events = [e for e in events if e.event_type.value == "CHAT_MESSAGE"]
    assert len(chat_events) >= 2
    assert chat_events[0].payload["content"] == "Primo"
    assert chat_events[1].payload["content"] == "Secondo"


def test_assistant_status_event(client: TestClient) -> None:
    session_id = "repair-status-001"
    with client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id=pc-01&device_type=pc&device_name=PC"
    ) as ws:
        ws.receive_json()
        ws.send_json({"type": "assistant_status", "status": "THINKING"})
        state_evt = ws.receive_json()
        assert state_evt["type"] == "event"
        assert state_evt["event"]["event_type"] == "SESSION_STATE_UPDATED"
        assert state_evt["event"]["payload"]["changes"]["assistant_status"] == "THINKING"
        legacy = ws.receive_json()
        assert legacy["event"]["event_type"] == "ASSISTANT_STATUS"
        assert legacy["event"]["payload"]["status"] == "THINKING"
        ws.receive_json()  # ack
