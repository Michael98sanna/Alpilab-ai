"""AI layer for Alpilab AI — provider abstraction and routing."""

from ai.router import AIRouter
from ai.providers import AIProvider, MockProvider

__all__ = ["AIRouter", "AIProvider", "MockProvider"]
