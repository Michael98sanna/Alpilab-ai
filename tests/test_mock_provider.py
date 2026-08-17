"""Tests for the offline mock AI provider."""

from ai.providers.mock import MOCK_BANNER, MockProvider
from ai.schemas import AIRequest, ImageInput, RequestKind


def test_mock_provider_is_available() -> None:
    provider = MockProvider()
    assert provider.name == "mock"
    assert provider.is_available() is True


def test_mock_provider_generate_marks_response_as_mock() -> None:
    provider = MockProvider()
    response = provider.generate(AIRequest(prompt="schermo nero"))
    assert response.is_mock is True
    assert response.provider_name == "mock"
    assert MOCK_BANNER in response.text
    assert "schermo nero" in response.text


def test_mock_provider_generate_with_image() -> None:
    provider = MockProvider()
    request = AIRequest(
        prompt="analisi foto connettore",
        kind=RequestKind.IMAGE,
        images=[ImageInput(filename="connector.jpg")],
    )
    response = provider.generate_with_image(request)
    assert response.is_mock is True
    assert "connector.jpg" in response.text
    assert "non analizzate" in response.text


def test_mock_provider_generate_with_image_requires_image() -> None:
    provider = MockProvider()
    try:
        provider.generate_with_image(AIRequest(prompt="senza foto"))
    except ValueError as exc:
        assert "image" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError when no image is provided")


def test_mock_provider_stream() -> None:
    provider = MockProvider()
    chunks = list(provider.generate_stream(AIRequest(prompt="test stream")))
    assert len(chunks) == 1
    assert MOCK_BANNER in chunks[0]
    assert "test stream" in chunks[0]
