"""AI provider implementations.

Real cloud/local providers will be added here later. They must implement
AIProvider and must never hard-code secrets.
"""

from ai.providers.base import AIProvider
from ai.providers.mock import MockProvider

__all__ = ["AIProvider", "MockProvider"]
