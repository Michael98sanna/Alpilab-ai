"""Tests for the AI router."""

import pytest

from ai.exceptions import NoAvailableProviderError, ProviderNotSupportedError
from ai.providers.base import AIProvider, ProviderCapabilities
from ai.providers.mock import MockProvider
from ai.router import AIRouter, RoutingHints, build_router
from ai.schemas import GenerationRequest, ImageGenerationRequest, ImageReference


class UnavailableProvider(AIProvider):
    name = "down"
    is_mock = True
    capabilities = ProviderCapabilities(supports_text=True, supports_images=False)

    def is_available(self) -> bool:
        return False

    def generate(self, request: GenerationRequest):
        raise AssertionError("unavailable provider must not be called")

    def generate_with_image(self, request: ImageGenerationRequest):
        raise AssertionError("unavailable provider must not be called")

    def generate_stream(self, request: GenerationRequest):
        raise AssertionError("unavailable provider must not be called")


def test_router_defaults_to_mock() -> None:
    router = AIRouter()
    assert router.provider_name == "mock"
    assert "mock" in router.provider_names


def test_router_ask_uses_mock_provider() -> None:
    router = AIRouter()
    text = router.ask("Batteria gonfia")
    assert "[MOCK]" in text
    assert "Batteria gonfia" in text


def test_router_skips_unavailable_providers() -> None:
    router = AIRouter(providers=[UnavailableProvider(), MockProvider()])
    response = router.generate(GenerationRequest(prompt="ping"))
    assert response.provider_name == "mock"


def test_router_requires_image_capable_provider() -> None:
    text_only = MockProvider()
    text_only.capabilities = ProviderCapabilities(
        supports_text=True,
        supports_images=False,
        is_local=True,
    )
    router = AIRouter(providers=[text_only], default_name="mock")

    with pytest.raises(NoAvailableProviderError):
        router.generate_with_image(
            ImageGenerationRequest(
                prompt="analizza",
                images=[ImageReference(filename="x.jpg")],
            )
        )


def test_build_router_rejects_unimplemented_provider() -> None:
    with pytest.raises(ProviderNotSupportedError):
        build_router("openai")


def test_routing_hints_prefer_default_when_available() -> None:
    router = AIRouter(providers=[MockProvider()], default_name="mock")
    chosen = router.select_provider(RoutingHints(prefer_local=True, prefer_low_cost=True))
    assert chosen.name == "mock"
