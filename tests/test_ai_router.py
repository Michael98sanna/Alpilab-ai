"""Tests for AI Router."""

from ai.providers.mock import MockProvider
from ai.router import AIRouter
from ai.schemas import AIRequest, RequestKind


def test_router_defaults_to_mock():
    router = AIRouter()
    assert router.provider_name == "mock"
    answer = router.ask("Batteria gonfia?")
    assert "Batteria gonfia?" in answer
    assert "[MOCK]" in answer


def test_router_uses_injected_provider():
    provider = MockProvider()
    router = AIRouter(provider=provider)
    assert router.active_provider is provider


def test_router_skips_unavailable_provider():
    unavailable = MockProvider(available=False)
    available = MockProvider(available=True)
    # Give the second instance a distinct name for assertion clarity.
    available.name = "mock_available"
    router = AIRouter(providers=[unavailable, available])
    assert router.provider_name == "mock_available"


def test_router_generate_with_image_kind():
    router = AIRouter()
    response = router.generate(
        AIRequest(
            prompt="Foto microscopio",
            kind=RequestKind.IMAGE,
            image_paths=["a.jpg"],
        )
    )
    assert response.is_mock is True
    assert response.kind == RequestKind.IMAGE


def test_router_list_providers():
    router = AIRouter(providers=[MockProvider(), MockProvider()])
    assert router.list_providers() == ["mock", "mock"]
