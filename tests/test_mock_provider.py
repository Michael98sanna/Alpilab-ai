"""Tests for MockProvider."""

from ai.providers.mock import MockProvider
from ai.schemas import AIRequest, RequestKind


def test_mock_provider_is_available():
    provider = MockProvider()
    assert provider.is_available() is True
    assert provider.name == "mock"


def test_mock_provider_generate():
    provider = MockProvider()
    response = provider.generate(AIRequest(prompt="Schermo nero iPhone 11"))
    assert response.is_mock is True
    assert response.provider_name == "mock"
    assert "Schermo nero iPhone 11" in response.content
    assert "[MOCK]" in response.content


def test_mock_provider_generate_with_image():
    provider = MockProvider()
    response = provider.generate_with_image(
        AIRequest(
            prompt="Analizza questa scheda",
            kind=RequestKind.IMAGE,
            image_paths=["/fake/board.jpg"],
        )
    )
    assert response.kind == RequestKind.IMAGE
    assert "Immagini allegate" in response.content
    assert response.metadata["image_count"] == 1


def test_mock_provider_generate_stream():
    provider = MockProvider()
    chunks = list(provider.generate_stream(AIRequest(prompt="test stream")))
    assert len(chunks) >= 1
    assert "test stream" in "".join(chunks)


def test_mock_provider_unavailable():
    provider = MockProvider(available=False)
    assert provider.is_available() is False
