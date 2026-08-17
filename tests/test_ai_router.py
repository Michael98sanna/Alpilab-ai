"""Tests for AI Router."""

from ai.providers.mock import MockProvider
from ai.router import AIRouter
from ai.schemas import AIGenerateRequest, AIImageGenerateRequest, RoutingHints


class UnavailableProvider(MockProvider):
    name = "unavailable"

    def is_available(self) -> bool:
        return False


def test_router_defaults_to_mock():
    router = AIRouter()
    assert router.provider_name == "mock"
    answer = router.ask("no power")
    assert "no power" in answer


def test_router_generate():
    router = AIRouter()
    result = router.generate(AIGenerateRequest(prompt="corto su PP_BATT"))
    assert result.provider == "mock"
    assert result.is_mock is True


def test_router_generate_with_image():
    router = AIRouter()
    result = router.generate_with_image(
        AIImageGenerateRequest(prompt="analizza", image_path="board.png")
    )
    assert result.is_mock is True
    assert "board.png" in result.content


def test_router_fallback_when_primary_unavailable():
    primary = UnavailableProvider()
    fallback = MockProvider()
    router = AIRouter(provider=primary, fallback_providers=[fallback])
    selected = router.select_provider(RoutingHints())
    assert selected.name == "mock"
    result = router.generate(AIGenerateRequest(prompt="fallback check"))
    assert result.provider == "mock"
