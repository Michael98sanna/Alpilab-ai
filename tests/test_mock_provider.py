"""Tests for MockProvider."""

from ai.providers.mock import MOCK_PREFIX, MockProvider
from ai.schemas import AIGenerateRequest, AIImageGenerateRequest


def test_mock_provider_available():
    provider = MockProvider()
    assert provider.is_available() is True
    assert provider.name == "mock"
    assert provider.is_local is True


def test_mock_provider_generate():
    provider = MockProvider()
    response = provider.generate(AIGenerateRequest(prompt="Batteria non carica"))
    assert response.is_mock is True
    assert response.provider == "mock"
    assert MOCK_PREFIX in response.content
    assert "Batteria non carica" in response.content


def test_mock_provider_generate_with_image():
    provider = MockProvider()
    response = provider.generate_with_image(
        AIImageGenerateRequest(
            prompt="Cosa vedi sulla scheda?",
            image_path="/tmp/fake.jpg",
        )
    )
    assert response.is_mock is True
    assert "fake.jpg" in response.content
    assert MOCK_PREFIX in response.content


def test_mock_provider_stream():
    provider = MockProvider()
    chunks = list(provider.generate_stream(AIGenerateRequest(prompt="test stream")))
    assert len(chunks) >= 1
    assert MOCK_PREFIX in "".join(chunks)


def test_mock_provider_ask_helper():
    provider = MockProvider()
    text = provider.ask("schermo nero")
    assert "schermo nero" in text
