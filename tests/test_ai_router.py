"""Tests for AI Router."""

from ai.providers.mock import MockProvider
from ai.router import AIRouter, build_default_router
from ai.schemas import AIAskRequest, RoutePreference


def test_router_uses_mock_by_default():
    router = AIRouter()
    assert router.provider_name == "mock"
    assert "mock" in router.available_providers()


def test_router_ask():
    router = AIRouter(provider=MockProvider())
    answer = router.ask("corto su PMIC")
    assert "corto su PMIC" in answer


def test_router_decide_accepts_future_preferences():
    router = AIRouter()
    decision = router.decide(
        preference=RoutePreference.LOCAL,
        has_images=True,
        kind="image_analysis",
    )
    assert decision.provider_name == "mock"
    assert "Phase-1" in decision.reason


def test_router_ask_structured():
    router = AIRouter()
    response = router.ask_structured(
        AIAskRequest(prompt="diagnosi display", has_images=False)
    )
    assert response.provider == "mock"
    assert "diagnosi display" in response.answer


def test_build_default_router_falls_back_to_mock():
    class FakeSettings:
        ai_provider = "openai"  # not implemented yet

    router = build_default_router(FakeSettings())
    assert router.provider_name == "mock"
