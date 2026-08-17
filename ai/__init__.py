"""AI layer for Alpilab AI (provider abstraction + router)."""

from .router import AIRouter
from .providers import AIProvider, MockProvider

__all__ = ["AIRouter", "AIProvider", "MockProvider"]
