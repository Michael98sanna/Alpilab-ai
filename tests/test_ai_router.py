"""Tests for AI Router."""

from ai.providers.base import AIProvider
from ai.providers.mock import MockProvider
from ai.router import AIRouter
from ai.schemas import AIRequest, AIResponse, RequestKind


class UnavailableProvider(AIProvider):
    name = "unavailable"

    def is_available(self) -> bool:
        return False

    def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(content="should not run", provider=self.name)

    def generate_with_image(self, request: AIRequest) -> AIResponse:
        return self.generate(request)

    def generate_stream(self, request: AIRequest):
        yield "nope"


def test_router_defaults_to_mock():
    router = AIRouter()
    assert router.provider_name == "mock"
    answer = router.ask("Non si accende")
    assert "Non si accende" in answer


def test_router_generate_text():
    router = AIRouter(provider=MockProvider())
    response = router.generate(AIRequest(prompt="Touches non rispondono"))
    assert response.provider == "mock"
    assert response.kind == RequestKind.GENERAL


def test_router_routes_images_to_generate_with_image():
    router = AIRouter()
    response = router.generate(
        AIRequest(
            prompt="Guarda il connettore",
            kind=RequestKind.IMAGE,
            image_paths=["connector.png"],
        )
    )
    assert response.kind == RequestKind.IMAGE
    assert "connector.png" in response.content


def test_router_fallback_when_primary_unavailable():
    fallback = MockProvider()
    router = AIRouter(
        provider=UnavailableProvider(),
        fallback_providers=[fallback],
    )
    selected = router.select_provider(AIRequest(prompt="x"))
    assert selected.name == "mock"
