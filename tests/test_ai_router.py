"""Tests for AIRouter."""

from ai.providers.base import AIProvider
from ai.providers.mock import MockProvider
from ai.router import AIRouter
from ai.schemas import AIRequest, AIResponse, RequestKind


class UnavailableProvider(AIProvider):
    name = "down"

    def is_available(self) -> bool:
        return False

    def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(content="should not run", provider=self.name)


def test_router_defaults_to_mock():
    router = AIRouter()
    assert router.provider_name == "mock"
    assert router.is_ready() is True


def test_router_ask():
    router = AIRouter()
    answer = router.ask("schermo nero")
    assert "schermo nero" in answer
    assert "MOCK" in answer


def test_router_generate_with_kind():
    router = AIRouter()
    response = router.generate(
        AIRequest(prompt="cortocircuito", kind=RequestKind.DIAGNOSIS)
    )
    assert response.provider == "mock"
    assert "cortocircuito" in response.content


def test_router_selects_fallback_when_primary_down():
    router = AIRouter(
        provider=UnavailableProvider(),
        fallback_providers=[MockProvider()],
    )
    selected = router.select_provider(AIRequest(prompt="x"))
    assert selected.name == "mock"
    response = router.generate(AIRequest(prompt="fallback ok"))
    assert "fallback ok" in response.content


def test_router_raises_when_nothing_available():
    router = AIRouter(provider=UnavailableProvider(), fallback_providers=[])
    try:
        router.select_provider(AIRequest(prompt="x"))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "disponibile" in str(exc).lower()


def test_router_image_path_uses_generate_with_image():
    router = AIRouter()
    response = router.generate(
        AIRequest(
            prompt="board view",
            kind=RequestKind.IMAGE_ANALYSIS,
            image_paths=("board.png",),
        )
    )
    assert "Immagini ricevute" in response.content
