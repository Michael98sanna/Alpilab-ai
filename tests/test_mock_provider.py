"""Tests for MockProvider."""

from ai.providers.mock import MockProvider
from ai.schemas import AIRequest, ProviderCapability, RequestKind


def test_mock_provider_available():
    provider = MockProvider()
    assert provider.is_available() is True
    assert provider.name == "mock"


def test_mock_provider_generate():
    provider = MockProvider()
    response = provider.generate(AIRequest(prompt="iPhone non si accende"))
    assert response.provider == "mock"
    assert response.model == "mock-v1"
    assert "MOCK" in response.content
    assert "iPhone non si accende" in response.content
    assert response.metadata.get("mock") is True


def test_mock_provider_ask_convenience():
    provider = MockProvider()
    text = provider.ask("test diagnosi")
    assert "test diagnosi" in text
    assert "MOCK" in text


def test_mock_provider_generate_with_image():
    provider = MockProvider()
    request = AIRequest(
        prompt="analizza questa scheda",
        kind=RequestKind.IMAGE_ANALYSIS,
        image_paths=("photo.jpg",),
    )
    response = provider.generate_with_image(request)
    assert "Immagini ricevute: 1" in response.content


def test_mock_provider_generate_with_image_requires_image():
    provider = MockProvider()
    try:
        provider.generate_with_image(AIRequest(prompt="senza immagini"))
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "image" in str(exc).lower()


def test_mock_provider_stream():
    provider = MockProvider()
    chunks = list(provider.generate_stream(AIRequest(prompt="stream test")))
    assert len(chunks) >= 1
    assert chunks[-1].done is True
    joined = "".join(c.content for c in chunks)
    assert "stream test" in joined


def test_mock_provider_capabilities():
    provider = MockProvider()
    assert ProviderCapability.TEXT in provider.capabilities
    assert ProviderCapability.LOCAL in provider.capabilities
