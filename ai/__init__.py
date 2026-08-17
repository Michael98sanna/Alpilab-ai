"""AI layer for Alpilab AI — provider abstraction and routing."""

from ai.router import AIRouter
from ai.schemas import AIRequest, AIResponse, RequestKind

__all__ = ["AIRouter", "AIRequest", "AIResponse", "RequestKind"]
