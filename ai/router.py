"""Provider router for Alpilab AI."""

from .providers.base import AIProvider
from .providers.mock import MockProvider


class AIRouter:
    """Selects the AI backend without exposing provider details to the app."""

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or MockProvider()

    @property
    def provider_name(self) -> str:
        return self._provider.name

    def ask(self, prompt: str) -> str:
        return self._provider.ask(prompt)
