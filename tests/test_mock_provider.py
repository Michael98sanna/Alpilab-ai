"""Tests for MockProvider."""

from ai.providers.mock import MockProvider
from ai.schemas import AIRequest, RequestKind


def test_mock_provider_is_available():
    provider = MockProvider()
    assert provider.is_available() is True
    assert provider.name == "mock"


def test_mock_provider_generate():
    provider = MockProvider()
    response = provider.generate(AIRequest(prompt="Schermo nero dopo caduta"))
    assert response.provider == "mock"
    assert "Schermo nero dopo caduta" in response.content
    assert response.metadata.get("mock") is True


def test_mock_provider_generate_with_image():
    provider = MockProvider()
    response = provider.generate_with_image(
        AIRequest(
            prompt="Analizza la scheda",
            kind=RequestKind.IMAGE,
            image_paths=["/tmp/board.jpg"],
        )
    )
    assert response.kind == RequestKind.IMAGE
    assert "/tmp/board.jpg" in response.content
    assert response.metadata.get("image_count") == 1


def test_mock_provider_stream():
    provider = MockProvider()
    chunks = list(provider.generate_stream(AIRequest(prompt="test stream")))
    assert len(chunks) >= 1
    assert "MOCK" in "".join(chunks)


def test_mock_provider_ask_helper():
    provider = MockProvider()
    text = provider.ask("Batteria gonfia?")
    assert "Batteria gonfia?" in text
