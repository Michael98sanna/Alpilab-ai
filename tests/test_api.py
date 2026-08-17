"""Smoke tests for the HTTP API."""

from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "mock"
    assert body["phase"] == "foundation"


def test_assistant_ask_uses_mock() -> None:
    response = client.post("/api/v1/assistant/ask", json={"question": "Non carica"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_mock"] is True
    assert "Non carica" in body["text"]


def test_frontend_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Alpilab AI" in response.text
