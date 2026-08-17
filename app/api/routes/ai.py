"""AI endpoints (stub for future web/mobile clients)."""

from ai.router import AIRouter
from ai.schemas import AIRequest, AIResponse


def generate_text(request: AIRequest, router: AIRouter | None = None) -> AIResponse:
    """
    Generate an AI response for a text prompt.

    Wired to MockProvider via AIRouter. Real providers will be added later
    without changing the API contract.
    """
    active_router = router or AIRouter()
    return active_router.generate(request)
