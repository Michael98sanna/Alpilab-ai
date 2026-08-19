"""V0.5.2 mobile client foundation: pairing identity, WS auth, RepairSession."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pairing.service import PairingService
from app.realtime.session_manager import realtime_manager
from app.security.client_auth import ClientAuthError, authorize_session_client
from app.session.factory import reset_session_store_cache
from app.session.sqlite_store import SQLiteSessionStore


@pytest.fixture
def sqlite_hub(tmp_path, monkeypatch):
    monkeypatch.setenv("ALPILAB_SESSION_STORE", "sqlite")
    monkeypatch.setenv("ALPILAB_SQLITE_PATH", str(tmp_path / "mobile.db"))
    monkeypatch.setenv("ALPILAB_REQUIRE_CLIENT_PAIRING", "true")
    reset_session_store_cache()
    realtime_manager._sessions.clear()
    realtime_manager._ws_connections.clear()
    realtime_manager._event_log.clear()
    yield TestClient(app)
    monkeypatch.delenv("ALPILAB_REQUIRE_CLIENT_PAIRING", raising=False)
    monkeypatch.delenv("ALPILAB_SESSION_STORE", raising=False)
    reset_session_store_cache()
    realtime_manager._sessions.clear()


def _pair(client: TestClient, device_id: str = "phone-stable-01") -> dict:
    start = client.post("/api/v1/pairing/start")
    assert start.status_code == 200
    done = client.post(
        "/api/v1/pairing/complete",
        json={
            "code": start.json()["code"],
            "client_id": device_id,
            "client_type": "phone",
            "platform": "android",
            "device_name": "Pixel",
        },
    )
    assert done.status_code == 200
    return done.json()


def test_pairing_persists_device_id_and_token(tmp_path) -> None:
    store = SQLiteSessionStore(tmp_path / "id.db")
    svc = PairingService(store)
    started = svc.start()
    result = svc.complete(
        started["code"],
        client_id="phone-stable-01",
        client_type="phone",
        platform="android",
        device_name="Pixel",
    )
    assert result["client_id"] == "phone-stable-01"
    assert result["token"]
    assert svc.is_authorized("phone-stable-01", result["token"])
    store.close()
    store2 = SQLiteSessionStore(tmp_path / "id.db")
    svc2 = PairingService(store2)
    assert svc2.is_authorized("phone-stable-01", result["token"])
    assert not svc2.is_authorized("device-other", result["token"])


def test_valid_token_wrong_device_id_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ALPILAB_SESSION_STORE", "sqlite")
    monkeypatch.setenv("ALPILAB_SQLITE_PATH", str(tmp_path / "wrong.db"))
    monkeypatch.setenv("ALPILAB_REQUIRE_CLIENT_PAIRING", "true")
    reset_session_store_cache()
    store = SQLiteSessionStore(tmp_path / "wrong.db")
    svc = PairingService(store)
    started = svc.start()
    result = svc.complete(
        started["code"],
        client_id="phone-stable-01",
        client_type="phone",
        platform="android",
        device_name="Pixel",
    )
    assert not svc.is_authorized("device-xxxxxxxx", result["token"])
    with pytest.raises(ClientAuthError) as exc:
        authorize_session_client(
            host="192.168.0.20",
            device_id="device-xxxxxxxx",
            device_type="phone",
            pairing_token=result["token"],
        )
    assert exc.value.code == "UNAUTHORIZED"
    monkeypatch.delenv("ALPILAB_REQUIRE_CLIENT_PAIRING", raising=False)
    monkeypatch.delenv("ALPILAB_SESSION_STORE", raising=False)
    reset_session_store_cache()


def test_paired_client_uses_hub_default_session(sqlite_hub: TestClient) -> None:
    info = sqlite_hub.get("/api/v1/hub/info").json()
    assert info["default_session_id"] == "repair-001"
    paired = _pair(sqlite_hub)
    assert paired["session_id"] == info["default_session_id"]
    assert paired["session_id"] == "repair-001"


def test_ws_authorized_with_matching_token_and_device_id(sqlite_hub: TestClient) -> None:
    paired = _pair(sqlite_hub, "phone-stable-01")
    session_id = paired["session_id"]
    token = paired["token"]
    with sqlite_hub.websocket_connect(
        f"/ws/sessions/{session_id}"
        f"?device_id=phone-stable-01&device_type=phone&device_name=Pixel"
        f"&pairing_token={token}"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "snapshot"
        assert msg["payload"]["session"]["id"] == "repair-001"


def test_ws_rejected_when_device_id_does_not_match_token(sqlite_hub: TestClient) -> None:
    paired = _pair(sqlite_hub, "phone-stable-01")
    token = paired["token"]
    session_id = paired["session_id"]
    with sqlite_hub.websocket_connect(
        f"/ws/sessions/{session_id}"
        f"?device_id=device-xxxxxxxx&device_type=phone&device_name=Pixel"
        f"&pairing_token={token}"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["message"] == "UNAUTHORIZED"


def test_ws_rejected_when_token_revoked(sqlite_hub: TestClient) -> None:
    paired = _pair(sqlite_hub, "phone-stable-01")
    token = paired["token"]
    session_id = paired["session_id"]
    revoked = sqlite_hub.delete("/api/v1/pairing/clients/phone-stable-01")
    assert revoked.status_code == 200
    with sqlite_hub.websocket_connect(
        f"/ws/sessions/{session_id}"
        f"?device_id=phone-stable-01&device_type=phone&device_name=Pixel"
        f"&pairing_token={token}"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["message"] == "UNAUTHORIZED"


def test_ws_rejected_when_device_not_paired(sqlite_hub: TestClient) -> None:
    with sqlite_hub.websocket_connect(
        "/ws/sessions/repair-001?device_id=phone-new&device_type=phone&device_name=Pixel"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["message"] in {"PAIRING_REQUIRED", "UNAUTHORIZED"}


def test_pc_loopback_client_still_skips_pairing(sqlite_hub: TestClient) -> None:
    with sqlite_hub.websocket_connect(
        "/ws/sessions/repair-001?device_id=pc-local&device_type=pc&device_name=PC"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "snapshot"
        assert msg["payload"]["session"]["id"] == "repair-001"


def test_pc_agent_ws_route_unchanged() -> None:
    routes = {getattr(r, "path", None) for r in app.routes}
    assert "/ws/agent/{session_id}" in routes
    assert "/ws/sessions/{session_id}" in routes
