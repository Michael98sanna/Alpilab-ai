"""Common interface implemented by every AI provider."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Provider-agnostic interface for text generation."""

    name: str = "unknown"

    @abstractmethod
    def ask(self, prompt: str) -> str:
        """Return an answer for a user prompt."""
        raise NotImplementedError
