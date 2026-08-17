"""Tests for AIRouter."""

from ai.providers.mock import MockProvider
from ai.router import AIRouter
from ai.schemas import AIRequest, ImageInput


def test_router_defaults_to_mock_provider() -> None:
    router = AIRouter()
    assert router.provider_name == "mock"


def test_router_generate_text() -> None:
    router = AIRouter()
    response = router.generate(AIRequest(prompt="Problema di ricarica"))
    assert response.provider == "mock"
    assert "Problema di ricarica" in response.content


def test_router_generate_with_images() -> None:
    router = AIRouter()
    request = AIRequest(
        prompt="Controlla il connettore",
        images=[ImageInput(reference="connector.jpg")],
    )
    response = router.generate(request)
    assert "Immagini ricevute: 1" in response.content


def test_router_generate_stream() -> None:
    router = AIRouter()
    chunks = list(router.generate_stream(AIRequest(prompt="stream test")))
    assert len(chunks) > 0


def test_router_ask_convenience() -> None:
    router = AIRouter(providers=[MockProvider()])
    answer = router.ask("Domanda semplice")
    assert "Domanda semplice" in answer
