"""Tests for MockProvider."""

from ai.providers.mock import MockProvider
from ai.schemas import AIGenerateRequest, AIImageInput, RequestKind


def test_mock_provider_is_available() -> None:
    provider = MockProvider()
    assert provider.is_available() is True
    assert provider.name == "mock"


def test_mock_provider_generate() -> None:
    provider = MockProvider()
    response = provider.generate(
        AIGenerateRequest(prompt="Schermo nero iPhone 12", kind=RequestKind.DIAGNOSIS)
    )
    assert response.is_mock is True
    assert response.provider == "mock"
    assert "Schermo nero iPhone 12" in response.content
    assert "[MOCK PROVIDER]" in response.content


def test_mock_provider_generate_with_image() -> None:
    provider = MockProvider()
    response = provider.generate_with_image(
        AIGenerateRequest(prompt="Analizza questa scheda"),
        AIImageInput(description="foto microscopio zona PMIC"),
    )
    assert response.is_mock is True
    assert "foto microscopio zona PMIC" in response.content


def test_mock_provider_generate_stream() -> None:
    provider = MockProvider()
    chunks = list(provider.generate_stream(AIGenerateRequest(prompt="test stream")))
    assert len(chunks) >= 1
    assert "MOCK PROVIDER" in "".join(chunks)
