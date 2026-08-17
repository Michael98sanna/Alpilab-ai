"""Lightweight route registry for future HTTP framework integration."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class APIRoute:
    """Describes one HTTP endpoint without binding to a specific framework."""

    path: str
    method: str
    handler: Callable[..., Any]
    name: str
    tags: tuple[str, ...] = ()


class APIRouteRegistry:
    """Collects API routes for future FastAPI/Starlette wiring."""

    def __init__(self) -> None:
        self._routes: list[APIRoute] = []

    def add(
        self,
        path: str,
        method: str,
        handler: Callable[..., Any],
        name: str,
        tags: tuple[str, ...] = (),
    ) -> None:
        self._routes.append(
            APIRoute(
                path=path,
                method=method.upper(),
                handler=handler,
                name=name,
                tags=tags,
            )
        )

    def routes(self) -> list[APIRoute]:
        return list(self._routes)
