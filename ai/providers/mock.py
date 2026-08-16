"""Offline provider used while the real AI integrations are being built."""

from .base import AIProvider


class MockProvider(AIProvider):
    name = "mock"

    def ask(self, prompt: str) -> str:
        return (
            "Provider di test attivo. La domanda ricevuta è: "
            f"{prompt}\n\n"
            "Il prossimo step sarà collegare un vero modello AI."
        )
