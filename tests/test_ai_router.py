"""Tests for AI Router."""

from ai.providers.mock import MockProvider
from ai.router import AIRouter
from ai.schemas import AIGenerateRequest, AIImageInput, ProviderCapability


class UnavailableProvider(MockProvider):
    name = "unavailable"

    def is_available(self) -> bool:
        return False


def test_router_defaults_to_mock() -> None:
    router = AIRouter()
    assert router.provider_name == "mock"
    answer = router.ask("Batteria gonfia?")
    assert "Batteria gonfia?" in answer
    assert "MOCK" in answer.upper() or "mock" in answer.lower()


def test_router_generate() -> None:
    router = AIRouter()
    response = router.generate(AIGenerateRequest(prompt="No power"))
    assert response.provider == "mock"
    assert response.is_mock is True


def test_router_skips_unavailable_provider() -> None:
    router = AIRouter(providers=[UnavailableProvider(), MockProvider()])
    assert router.select_provider().name == "mock"


def test_router_prefer_local_and_image() -> None:
    router = AIRouter()
    request = AIGenerateRequest(prompt="x", prefer_local=True, require_image=True)
    provider = router.select_provider(request)
    assert provider.supports(ProviderCapability.IMAGE)
    assert provider.supports(ProviderCapability.LOCAL)


def test_router_generate_with_image() -> None:
    router = AIRouter()
    response = router.generate_with_image(
        AIGenerateRequest(prompt="boardview"),
        AIImageInput(path="/tmp/mock.jpg"),
    )
    assert response.is_mock is True
    assert response.metadata.get("has_image") is True
