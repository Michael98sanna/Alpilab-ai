"""AI provider implementations.

Only MockProvider is registered in this phase. Real vendor SDKs must not
be imported here until a dedicated provider module is added.
"""

from .base import AIProvider, ProviderCapabilities
from .mock import MockProvider

__all__ = ["AIProvider", "MockProvider", "ProviderCapabilities"]
