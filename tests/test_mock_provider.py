"""Tests for MockProvider."""

from ai.providers.base import GenerationRequest
from ai.providers.mock import MockProvider


def test_mock_provider_available():
    provider = MockProvider()
    assert provider.is_available() is True
    assert provider.name == "mock"


def test_mock_provider_generate():
    provider = MockProvider()
    result = provider.generate(GenerationRequest(prompt="iPhone non si accende"))
    assert result.provider == "mock"
    assert "iPhone non si accende" in result.text
    assert result.metadata.get("mock") is True


def test_mock_provider_ask_convenience():
    provider = MockProvider()
    text = provider.ask("test batteria")
    assert "test batteria" in text


def test_mock_provider_generate_with_image():
    provider = MockProvider()
    result = provider.generate_with_image(
        GenerationRequest(prompt="analizza board", images=[b"fake-image-bytes"])
    )
    assert "immagini ricevute: 1" in result.text


def test_mock_provider_stream():
    provider = MockProvider()
    chunks = list(provider.generate_stream(GenerationRequest(prompt="stream test")))
    assert len(chunks) == 2
    assert "stream test" in "".join(chunks)
