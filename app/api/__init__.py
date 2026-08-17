"""HTTP API layer prepared for future web and mobile clients."""

from app.api.router import APIRouteRegistry
from app.api.routes import generate_text, get_health
from app.api.schemas import ErrorResponse, HealthResponse

__all__ = [
    "APIRouteRegistry",
    "ErrorResponse",
    "HealthResponse",
    "create_route_registry",
    "generate_text",
    "get_health",
]


def create_route_registry() -> APIRouteRegistry:
    """Register foundation endpoints. Framework binding happens in a later phase."""
    registry = APIRouteRegistry()
    registry.add(
        path="/health",
        method="GET",
        handler=get_health,
        name="health",
        tags=("system",),
    )
    registry.add(
        path="/api/v1/ai/generate",
        method="POST",
        handler=generate_text,
        name="ai_generate",
        tags=("ai",),
    )
    return registry
