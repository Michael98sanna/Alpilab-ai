"""Tests for the AI Router."""

from ai.providers.base import AIProvider, ProviderCapabilities
from ai.providers.mock import MOCK_BANNER, MockProvider
from ai.router import AIRouter, NoProviderAvailable
from ai.schemas import AIRequest, ImageInput


class UnavailableProvider(AIProvider):
    name = "down"
    capabilities = ProviderCapabilities(text=True)

    def is_available(self) -> bool:
        return False

    def generate(self, request: AIRequest):
        raise AssertionError("unavailable provider must not be called")

    def generate_with_image(self, request: AIRequest):
        raise AssertionError("unavailable provider must not be called")

    def generate_stream(self, request: AIRequest):
        raise AssertionError("unavailable provider must not be called")


def test_router_defaults_to_mock_provider() -> None:
    router = AIRouter()
    assert router.provider_name == "mock"
    text = router.ask("non si carica")
    assert MOCK_BANNER in text
    assert "non si carica" in text


def test_router_generate_uses_selected_provider() -> None:
    router = AIRouter(providers=[MockProvider()])
    response = router.generate(AIRequest(prompt="batteria gonfia"))
    assert response.provider_name == "mock"
    assert response.is_mock is True


def test_router_routes_images_to_generate_with_image() -> None:
    router = AIRouter()
    response = router.generate(
        AIRequest(
            prompt="foto board",
            images=[ImageInput(filename="board.png")],
        )
    )
    assert "board.png" in response.text


def test_router_skips_unavailable_provider() -> None:
    router = AIRouter(providers=[UnavailableProvider(), MockProvider()])
    selected = router.select_provider(AIRequest(prompt="x"))
    assert selected.name == "mock"


def test_router_raises_when_nothing_is_available() -> None:
    router = AIRouter(providers=[UnavailableProvider()])
    try:
        router.select_provider(AIRequest(prompt="x"))
    except NoProviderAvailable:
        return
    raise AssertionError("Expected NoProviderAvailable")


def test_router_honours_preferred_provider_name() -> None:
    first = MockProvider()
    second = MockProvider()
    second.name = "mock-b"
    router = AIRouter(providers=[first, second])
    selected = router.select_provider(AIRequest(prompt="x", preferred_provider="mock-b"))
    assert selected is second
