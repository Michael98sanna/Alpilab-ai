"""Shared security primitives.

This module does not execute commands and does not grant access by default.
Hardware and PC actions must go through explicit permissions and, when
dangerous, through an explicit confirmation flag.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class PermissionDenied(Exception):
    """Raised when the caller is not allowed to perform an action."""


class ConfirmationRequired(Exception):
    """Raised when a potentially dangerous action was not confirmed."""


@dataclass(frozen=True)
class PermissionContext:
    """Who is asking and which named actions they may perform."""

    actor: str
    allowed_actions: frozenset[str] = field(default_factory=frozenset)

    def can(self, action: str) -> bool:
        return action in self.allowed_actions

    def require(self, action: str) -> None:
        if not self.can(action):
            raise PermissionDenied(
                f"Actor '{self.actor}' is not allowed to perform '{action}'."
            )


def require_confirmation(confirmed: bool, action: str) -> None:
    """Dangerous actions must pass confirmed=True. Nothing is executed here."""

    if not confirmed:
        raise ConfirmationRequired(
            f"Action '{action}' is potentially dangerous and requires explicit confirmation."
        )
