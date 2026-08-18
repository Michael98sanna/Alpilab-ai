"""Local Hub API, LocalAIProvider, discovery helpers."""

import pytest
from fastapi.testclient import TestClient

from ai.providers.local import LocalAIProvider
from ai.schemas import AIRequest
from app.hub.discovery import detect_lan_ip
from app.main import app
from app.realtime.session_manager import realtime_manager
from app.session.factory import reset_session_store_cache


@pytest.fixture(autouse=True)
def _reset_hub_state():
    yield
    reset_session_store_cache()
    realtime_manager._persistence_store = None


def test_local_ai_unconfigured() -> None:
    provider = LocalAIProvider(None)
    assert provider.is_available() is False
    response = provider.generate(AIRequest(prompt="ciao"))
    assert "non configurato" in response.content.lower() or "MockProvider" in response.content


def test_hub_info_endpoint() -> None:
    client = TestClient(app)
    res = client.get("/api/v1/hub/info")
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Alpilab Negozio"
    assert body["default_session_id"] == "repair-001"
    assert body["mode"] == "local-first"
    assert "lan_url" in body


def test_pairing_requires_sqlite(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPILAB_SESSION_STORE", "sqlite")
    monkeypatch.setenv("ALPILAB_SQLITE_PATH", str(tmp_path / "hub.db"))
    reset_session_store_cache()
    client = TestClient(app)
    start = client.post("/api/v1/pairing/start")
    assert start.status_code == 200
    code = start.json()["code"]
    done = client.post(
        "/api/v1/pairing/complete",
        json={
            "code": code,
            "client_type": "phone",
            "platform": "android",
            "device_name": "TestPhone",
        },
    )
    assert done.status_code == 200
    assert done.json()["status"] == "authorized"
    listed = client.get("/api/v1/pairing/clients")
    assert listed.status_code == 200
    assert listed.json()["clients"][0]["device_name"] == "TestPhone"
    reset_session_store_cache()


def test_detect_lan_ip() -> None:
    ip = detect_lan_ip()
    assert isinstance(ip, str)
    assert ip
