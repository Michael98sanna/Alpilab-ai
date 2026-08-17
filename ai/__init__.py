"""AI layer for Alpilab AI.

This package owns provider abstraction, routing, prompts, and AI-specific schemas.
Application code should talk to AIRouter, not to individual providers.
"""

from ai.router import AIRouter
from ai.schemas import AIRequest, AIResponse, RequestKind

__all__ = ["AIRouter", "AIRequest", "AIResponse", "RequestKind"]
