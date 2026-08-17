"""Smoke tests for the HTTP API."""

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app(Settings(ai_provider="mock", app_env="test")))
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "alpilab-ai"
    assert payload["ai_provider"] == "mock"


def test_generate_endpoint_uses_mock_provider() -> None:
    client = TestClient(create_app(Settings()))
    response = client.post("/api/ai/generate", json={"prompt": "non si accende"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_mock"] is True
    assert payload["provider_name"] == "mock"
    assert "non si accende" in payload["text"]
    assert "[MOCK PROVIDER]" in payload["text"]
