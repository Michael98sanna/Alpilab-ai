"""AI layer for Alpilab AI."""

from ai.router import AIRouter, FallbackStrategy, SmartAIRouter
from ai.schemas import AIRequest, AIResponse

__all__ = ["AIRouter", "AIRequest", "AIResponse", "FallbackStrategy", "SmartAIRouter"]
