"""API route handlers grouped by domain."""

from .ai import generate_text
from .health import get_health

__all__ = ["generate_text", "get_health"]
