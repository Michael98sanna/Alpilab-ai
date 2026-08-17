"""AI provider implementations.

Only MockProvider is available in this phase. Real local and cloud providers
will be added as separate modules that implement AIProvider.
"""

from .base import AIProvider, ProviderCapabilities
from .mock import MockProvider

__all__ = ["AIProvider", "ProviderCapabilities", "MockProvider"]
