"""Tests for the offline MockProvider."""

from ai.providers.mock import MockProvider
from ai.schemas import GenerationRequest, ImageGenerationRequest, ImageReference


def test_mock_provider_is_available() -> None:
    provider = MockProvider()
    assert provider.name == "mock"
    assert provider.is_mock is True
    assert provider.is_available() is True


def test_mock_generate_echoes_prompt_and_marks_mock() -> None:
    provider = MockProvider()
    response = provider.generate(GenerationRequest(prompt="Il display non si accende"))

    assert response.is_mock is True
    assert response.provider_name == "mock"
    assert "[MOCK]" in response.text
    assert "Il display non si accende" in response.text
    assert response.confidence is None
    assert response.facts == []


def test_mock_generate_with_image_does_not_pretend_to_see_pixels() -> None:
    provider = MockProvider()
    response = provider.generate_with_image(
        ImageGenerationRequest(
            prompt="Cosa vedi sul PCB?",
            images=[ImageReference(filename="board.jpg")],
        )
    )

    assert response.is_mock is True
    assert "NON analizza" in response.text
    assert "board.jpg" in response.text


def test_mock_generate_stream_yields_text() -> None:
    provider = MockProvider()
    chunks = list(provider.generate_stream(GenerationRequest(prompt="test stream")))
    assert chunks
    assert "[MOCK]" in "".join(chunks)
