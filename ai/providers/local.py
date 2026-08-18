"""Optional local LLM provider (Ollama / llama.cpp) — not required for V0.5."""

from collections.abc import Iterator

from ai.providers.base import AIProvider
from ai.schemas import AIRequest, AIResponse, ProviderCapability


class LocalAIProvider(AIProvider):
    """
    Stub for a future on-device model.

    Never downloads models automatically. is_available() is False until a local
    runtime (e.g. Ollama) is configured via ALPILAB_LOCAL_AI_URL.
    """

    name = "local"

    def __init__(self, endpoint_url: str | None = None) -> None:
        self.endpoint_url = endpoint_url

    def is_available(self) -> bool:
        return bool(self.endpoint_url)

    def generate(self, request: AIRequest) -> AIResponse:
        if not self.is_available():
            return AIResponse(
                content=(
                    "Modello locale non configurato. "
                    "Alpilab funziona offline con MockProvider. "
                    "Per abilitare un LLM locale imposta ALPILAB_LOCAL_AI_URL "
                    "(Ollama/llama.cpp) senza dipendere dal cloud."
                ),
                provider=self.name,
                model="unconfigured",
                finish_reason="unavailable",
                metadata={"configured": False},
            )
        return AIResponse(
            content=f"[LOCAL STUB] Prompt: {request.prompt}",
            provider=self.name,
            model="local-stub",
            finish_reason="stop",
            metadata={"endpoint": self.endpoint_url, "stub": True},
        )

    def generate_with_image(self, request: AIRequest) -> AIResponse:
        return self.generate(request)

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        yield self.generate(request).content

    def capabilities(self) -> set[ProviderCapability]:
        return {ProviderCapability.TEXT_GENERATION, ProviderCapability.LOCAL}
