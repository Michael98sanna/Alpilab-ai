"""
Future HTTP server entry point for Alpilab AI.

This module registers API routes but does not start a web server yet.
A FastAPI/Starlette application will be wired here in a later phase.
"""

from app.api import create_route_registry


def get_registered_routes() -> list[tuple[str, str, str]]:
    """Return (method, path, name) tuples for diagnostics and tests."""
    registry = create_route_registry()
    return [(route.method, route.path, route.name) for route in registry.routes()]
