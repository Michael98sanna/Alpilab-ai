"""Smoke tests for the HTTP API foundation."""

from fastapi.testclient import TestClient

from app.api import create_app
from app.services import AssistantService
from ai.router import AIRouter


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["ai_provider"] == "mock"
    assert body["ready"] is True


def test_ask_endpoint():
    client = TestClient(create_app(AssistantService(AIRouter())))
    response = client.post("/v1/ask", json={"prompt": "non si accende"})
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert "non si accende" in body["content"]
    assert "MOCK" in body["content"]
