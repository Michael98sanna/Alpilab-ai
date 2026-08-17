"""Errors raised by the AI layer."""


class AILayerError(Exception):
    """Base class for AI routing and generation failures."""


class NoAvailableProviderError(AILayerError):
    """No registered provider is currently available."""


class ProviderNotSupportedError(AILayerError):
    """The requested provider name is not implemented in this phase."""
