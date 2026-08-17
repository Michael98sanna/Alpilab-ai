"""Tests for MockProvider."""

from ai.providers.mock import MockProvider
from ai.schemas import AIRequest, ImageInput, ProviderCapability


def test_mock_provider_is_available() -> None:
    provider = MockProvider()
    assert provider.is_available() is True


def test_mock_provider_generate() -> None:
    provider = MockProvider()
    response = provider.generate(AIRequest(prompt="Schermo nero dopo caduta"))
    assert response.provider == "mock"
    assert "MOCK" in response.content
    assert "Schermo nero dopo caduta" in response.content


def test_mock_provider_generate_with_image() -> None:
    provider = MockProvider()
    request = AIRequest(
        prompt="Analizza questa foto",
        images=[ImageInput(reference="photo.jpg")],
    )
    response = provider.generate_with_image(request)
    assert "Immagini ricevute: 1" in response.content


def test_mock_provider_generate_stream() -> None:
    provider = MockProvider()
    chunks = list(provider.generate_stream(AIRequest(prompt="test")))
    assert len(chunks) > 0
    assert "MOCK" in "".join(chunks)


def test_mock_provider_capabilities() -> None:
    provider = MockProvider()
    caps = provider.capabilities()
    assert ProviderCapability.TEXT_GENERATION in caps
    assert ProviderCapability.IMAGE_INPUT in caps
