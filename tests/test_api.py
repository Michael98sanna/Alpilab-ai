"""API smoke tests."""

from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["ai_provider"] == "mock"


def test_ai_ask():
    response = client.post("/api/ai/ask", json={"question": "No power on iPhone"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_mock"] is True
    assert body["provider"] == "mock"
    assert "No power" in body["answer"]
