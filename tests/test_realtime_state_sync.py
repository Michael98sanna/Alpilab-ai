"""Shared session state synchronization tests (realtime V1.1)."""

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


def _connect(client: TestClient, session_id: str, device_id: str, device_type: str, name: str):
    ws = client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id={device_id}&device_type={device_type}"
        f"&device_name={name}&seed_demo=true"
    )
    return ws.__enter__()


def _connect_session(client: TestClient, session_id: str, devices: list[tuple[str, str, str]]) -> list:
    """Connect multiple devices; drain DEVICE_CONNECTED on peers after each join."""
    sockets: list = []
    for device_id, device_type, name in devices:
        ws = _connect(client, session_id, device_id, device_type, name)
        _read_snapshot(ws)
        sockets.append(ws)
        for peer in sockets[:-1]:
            peer.receive_json()
    return sockets


def _recv_state_update(ws) -> dict:
    while True:
        msg = ws.receive_json()
        if msg.get("type") == "event" and msg["event"]["event_type"] == "SESSION_STATE_UPDATED":
            return msg


def _read_snapshot(ws) -> dict:
    msg = ws.receive_json()
    assert msg["type"] == "snapshot"
    return msg["payload"]


def test_snapshot_includes_state_version(client: TestClient) -> None:
    with _connect(client, "repair-snap-v", "pc-01", "pc", "PC") as ws:
        snap = _read_snapshot(ws)
        assert "state_version" in snap
        assert snap["state_version"] == 0
        assert len(snap["diagnostic_state"]) == 3


def test_diagnostic_measurement_update_broadcast(client: TestClient, manager: RealtimeSessionManager) -> None:
    session_id = "repair-measure-001"
    ws_pc, ws_phone = _connect_session(
        client,
        session_id,
        [("pc-01", "pc", "PC"), ("phone-01", "phone", "Phone")],
    )
    try:
        ws_phone.send_json(
            {"type": "diagnostic_update", "test_id": "t3", "value": "0.500"}
        )
        update_phone = _recv_state_update(ws_phone)
        payload = update_phone["event"]["payload"]
        assert payload["state_version"] == 1
        assert payload["changes"]["diagnostic_test"]["value"] == "0.500 V"
        assert payload["changes"]["diagnostic_test"]["status"] == "PASSED"
        ws_phone.receive_json()  # DIAGNOSTIC_UPDATED
        ws_phone.receive_json()  # ack

        update_pc = _recv_state_update(ws_pc)
        assert update_pc["event"]["payload"]["state_version"] == 1

        session = manager.get_session(session_id)
        assert session is not None
        t3 = next(t for t in session.diagnostics if t.id == "t3")
        assert t3.value == "0.500 V"
        assert t3.status == "PASSED"
    finally:
        ws_phone.__exit__(None, None, None)
        ws_pc.__exit__(None, None, None)


def test_multi_device_same_final_value(client: TestClient) -> None:
    session_id = "repair-multi-001"
    ws_pc, ws_phone, ws_tab = _connect_session(
        client,
        session_id,
        [
            ("pc-01", "pc", "PC"),
            ("phone-01", "phone", "Phone"),
            ("tablet-01", "tablet", "Tablet"),
        ],
    )
    try:
        ws_phone.send_json(
            {"type": "diagnostic_update", "test_id": "t3", "value": "0.500 V"}
        )
        phone_update = _recv_state_update(ws_phone)
        ws_phone.receive_json()
        ws_phone.receive_json()
        version = phone_update["event"]["payload"]["state_version"]

        pc_update = _recv_state_update(ws_pc)
        tab_update = _recv_state_update(ws_tab)
        assert pc_update["event"]["payload"]["state_version"] == version
        assert tab_update["event"]["payload"]["state_version"] == version
        for evt in (pc_update, tab_update):
            test = evt["event"]["payload"]["changes"]["diagnostic_test"]
            assert test["value"] == "0.500 V"
    finally:
        ws_tab.__exit__(None, None, None)
        ws_phone.__exit__(None, None, None)
        ws_pc.__exit__(None, None, None)


def test_diagnosis_pause_resume_sync(client: TestClient) -> None:
    session_id = "repair-pause-001"
    ws_pc, ws_phone = _connect_session(
        client,
        session_id,
        [("pc-01", "pc", "PC"), ("phone-01", "phone", "Phone")],
    )
    try:
        ws_pc.send_json({"type": "diagnosis_pause", "paused": True})
        pause_pc = _recv_state_update(ws_pc)
        assert pause_pc["event"]["payload"]["changes"]["repair_context"]["status"] == "paused"
        ws_pc.receive_json()

        pause_phone = _recv_state_update(ws_phone)
        assert pause_phone["event"]["payload"]["changes"]["repair_context"]["status"] == "paused"

        ws_phone.send_json({"type": "diagnosis_pause", "paused": False})
        resume_phone = _recv_state_update(ws_phone)
        assert resume_phone["event"]["payload"]["changes"]["repair_context"]["status"] == "active"
        ws_phone.receive_json()

        resume_pc = _recv_state_update(ws_pc)
        assert resume_pc["event"]["payload"]["changes"]["repair_context"]["status"] == "active"
    finally:
        ws_phone.__exit__(None, None, None)
        ws_pc.__exit__(None, None, None)


def test_assistant_status_via_state_update(client: TestClient) -> None:
    session_id = "repair-assist-001"
    ws_pc, ws_phone = _connect_session(
        client,
        session_id,
        [("pc-01", "pc", "PC"), ("phone-01", "phone", "Phone")],
    )
    try:
        ws_pc.send_json({"type": "assistant_status", "status": "THINKING"})
        state_evt = _recv_state_update(ws_pc)
        assert state_evt["event"]["payload"]["changes"]["assistant_status"] == "THINKING"
        ws_pc.receive_json()
        ws_pc.receive_json()

        phone_state = _recv_state_update(ws_phone)
        assert phone_state["event"]["payload"]["changes"]["assistant_status"] == "THINKING"
        ws_phone.receive_json()
    finally:
        ws_phone.__exit__(None, None, None)
        ws_pc.__exit__(None, None, None)


def test_repair_context_update_sync(client: TestClient) -> None:
    session_id = "repair-ctx-001"
    ws_pc, ws_phone = _connect_session(
        client,
        session_id,
        [("pc-01", "pc", "PC"), ("phone-01", "phone", "Phone")],
    )
    try:
        ws_pc.send_json(
            {
                "type": "repair_context_update",
                "device": "iPhone 14",
                "issue": "No charge",
            }
        )
        evt_pc = _recv_state_update(ws_pc)
        ctx = evt_pc["event"]["payload"]["changes"]["repair_context"]
        assert ctx["device"] == "iPhone 14"
        assert ctx["issue"] == "No charge"
        ws_pc.receive_json()

        evt_phone = _recv_state_update(ws_phone)
        assert evt_phone["event"]["payload"]["changes"]["repair_context"]["device"] == "iPhone 14"
    finally:
        ws_phone.__exit__(None, None, None)
        ws_pc.__exit__(None, None, None)


def test_rejected_invalid_measurement(client: TestClient) -> None:
    session_id = "repair-reject-001"
    with _connect(client, session_id, "pc-01", "pc", "PC") as ws:
        _read_snapshot(ws)
        ws.send_json({"type": "diagnostic_update", "test_id": "t3", "value": "not-a-number"})
        rejected = ws.receive_json()
        assert rejected["type"] == "event"
        assert rejected["event"]["event_type"] == "STATE_UPDATE_REJECTED"
        ws.receive_json()  # ack


def test_rejected_unknown_test(client: TestClient) -> None:
    session_id = "repair-reject-002"
    with _connect(client, session_id, "pc-01", "pc", "PC") as ws:
        _read_snapshot(ws)
        ws.send_json({"type": "diagnostic_update", "test_id": "missing", "value": "1.0"})
        rejected = ws.receive_json()
        assert rejected["event"]["event_type"] == "STATE_UPDATE_REJECTED"


def test_rejected_while_paused(client: TestClient) -> None:
    session_id = "repair-reject-003"
    with _connect(client, session_id, "pc-01", "pc", "PC") as ws:
        _read_snapshot(ws)
        ws.send_json({"type": "diagnosis_pause", "paused": True})
        ws.receive_json()
        ws.receive_json()
        ws.send_json({"type": "diagnostic_update", "test_id": "t3", "value": "0.5"})
        rejected = ws.receive_json()
        assert rejected["event"]["event_type"] == "STATE_UPDATE_REJECTED"


def test_state_version_monotonic(client: TestClient, manager: RealtimeSessionManager) -> None:
    session_id = "repair-version-001"
    with _connect(client, session_id, "pc-01", "pc", "PC") as ws:
        _read_snapshot(ws)
        ws.send_json({"type": "diagnostic_update", "test_id": "t3", "value": "0.5"})
        v1 = ws.receive_json()["event"]["payload"]["state_version"]
        ws.receive_json()
        ws.receive_json()
        ws.send_json({"type": "diagnostic_update", "test_id": "t2", "value": "0"})
        v2 = ws.receive_json()["event"]["payload"]["state_version"]
        assert v2 == v1 + 1
        session = manager.get_session(session_id)
        assert session is not None
        assert session.state_version == v2


def test_simultaneous_updates_serialized(client: TestClient, manager: RealtimeSessionManager) -> None:
    """Server serializes concurrent updates; final state is consistent."""
    session_id = "repair-race-001"
    ws_pc, ws_phone = _connect_session(
        client,
        session_id,
        [("pc-01", "pc", "PC"), ("phone-01", "phone", "Phone")],
    )
    try:
        ws_pc.send_json({"type": "diagnostic_update", "test_id": "t3", "value": "0.400"})
        ws_phone.send_json({"type": "diagnostic_update", "test_id": "t3", "value": "0.500"})

        seen_versions: set[int] = set()
        for ws in (ws_pc, ws_phone):
            for _ in range(4):
                msg = ws.receive_json()
                if msg.get("type") == "event" and msg["event"]["event_type"] == "SESSION_STATE_UPDATED":
                    seen_versions.add(msg["event"]["payload"]["state_version"])

        assert seen_versions == {1, 2}
        session = manager.get_session(session_id)
        assert session is not None
        assert session.state_version == 2
        t3 = next(t for t in session.diagnostics if t.id == "t3")
        assert t3.value in {"0.400 V", "0.500 V"}
    finally:
        ws_phone.__exit__(None, None, None)
        ws_pc.__exit__(None, None, None)


def test_reconnect_receives_full_snapshot(client: TestClient) -> None:
    session_id = "repair-reconnect-001"
    with _connect(client, session_id, "pc-01", "pc", "PC") as ws_pc:
        _read_snapshot(ws_pc)
        with _connect(client, session_id, "phone-01", "phone", "Phone") as ws_phone:
            _read_snapshot(ws_phone)
            ws_pc.receive_json()
            ws_phone.send_json({"type": "diagnostic_update", "test_id": "t2", "value": "0"})
            ws_phone.receive_json()
            ws_phone.receive_json()
            ws_phone.receive_json()
            ws_pc.receive_json()

        with _connect(client, session_id, "pc-01", "pc", "PC") as ws_pc2:
            snap = _read_snapshot(ws_pc2)
            assert snap["state_version"] >= 1
            t2 = next(t for t in snap["diagnostic_state"] if t["id"] == "t2")
            assert t2["status"] == "FAILED"


def test_request_snapshot_on_gap(client: TestClient) -> None:
    session_id = "repair-sync-req-001"
    with _connect(client, session_id, "pc-01", "pc", "PC") as ws:
        snap = _read_snapshot(ws)
        ws.send_json({"type": "diagnostic_update", "test_id": "t3", "value": "0.500"})
        ws.receive_json()
        ws.receive_json()
        ws.receive_json()

        ws.send_json({"type": "request_snapshot"})
        resync = ws.receive_json()
        assert resync["type"] == "snapshot"
        assert resync["payload"]["state_version"] > snap["state_version"]
        t3 = next(t for t in resync["payload"]["diagnostic_state"] if t["id"] == "t3")
        assert t3["value"] == "0.500 V"


def test_duplicate_state_version_on_server(client: TestClient, manager: RealtimeSessionManager) -> None:
    session_id = "repair-dup-001"
    with _connect(client, session_id, "pc-01", "pc", "PC") as ws:
        _read_snapshot(ws)
        ws.send_json({"type": "diagnostic_update", "test_id": "t3", "value": "0.500"})
        evt = ws.receive_json()
        version = evt["event"]["payload"]["state_version"]
        ws.receive_json()
        ws.receive_json()
        data = manager.get_session(session_id)
        assert data is not None
        assert data.state_version == version


def test_first_chat_message_seeds_diagnostics(client: TestClient, manager: RealtimeSessionManager) -> None:
    session_id = "repair-seed-chat"
    manager.clear_session_workspace(session_id)
    ws = client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id=pc-01&device_type=pc&device_name=PC"
    ).__enter__()
    try:
        snap = _read_snapshot(ws)
        assert snap["diagnostic_state"] == []

        ws.send_json({"type": "chat_message", "content": "iPhone non si accende", "role": "user"})
        ws.receive_json()  # CHAT_MESSAGE event
        # NL service may emit additional events before SESSION_STATE_UPDATED
        while True:
            msg = ws.receive_json()
            if (
                msg.get("type") == "event"
                and msg["event"]["event_type"] == "SESSION_STATE_UPDATED"
                and "diagnostics" in msg["event"]["payload"].get("changes", {})
            ):
                update = msg
                break
        diagnostics = update["event"]["payload"]["changes"]["diagnostics"]
        assert len(diagnostics) == 3
        assert diagnostics[2]["id"] == "t3"
        assert diagnostics[2]["status"] == "PENDING"

        session = manager.get_session(session_id)
        assert session is not None
        assert len(session.diagnostics) == 3
    finally:
        ws.close()


def test_request_snapshot_seeds_diagnostics_for_active_repair(
    client: TestClient, manager: RealtimeSessionManager
) -> None:
    session_id = "repair-snapshot-seed"
    manager.clear_session_workspace(session_id)
    ws = client.websocket_connect(
        f"/ws/sessions/{session_id}?device_id=pc-01&device_type=pc&device_name=PC"
    ).__enter__()
    try:
        snap = _read_snapshot(ws)
        assert snap["diagnostic_state"] == []

        ws.send_json({"type": "chat_message", "content": "Schermo nero", "role": "user"})
        while True:
            msg = ws.receive_json()
            if msg.get("type") == "ack":
                break

        ws.send_json({"type": "request_snapshot"})
        while True:
            msg = ws.receive_json()
            if msg.get("type") == "snapshot":
                diagnostics = msg["payload"]["diagnostic_state"]
                break
        assert len(diagnostics) == 3
        assert diagnostics[0]["name"] == "Battery voltage"
    finally:
        ws.close()
