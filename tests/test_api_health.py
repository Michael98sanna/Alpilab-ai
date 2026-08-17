"""Tests for API foundation layer."""

from app.api import create_route_registry, get_health
from app.api.routes.ai import generate_text
from app.main import get_registered_routes
from ai.schemas import AIRequest


def test_get_health() -> None:
    health = get_health()
    assert health.status == "ok"
    assert health.service == "alpilab-ai"
    assert health.ai_provider == "mock"


def test_route_registry_contains_foundation_endpoints() -> None:
    registry = create_route_registry()
    routes = registry.routes()
    paths = {(route.method, route.path) for route in routes}
    assert ("GET", "/health") in paths
    assert ("POST", "/api/v1/ai/generate") in paths


def test_get_registered_routes_helper() -> None:
    routes = get_registered_routes()
    assert any(route[1] == "/health" for route in routes)


def test_ai_generate_route_handler() -> None:
    response = generate_text(AIRequest(prompt="Test API"))
    assert response.provider == "mock"
    assert "Test API" in response.content
