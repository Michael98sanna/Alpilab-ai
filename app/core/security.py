"""Security helpers and policy stubs.

Phase 1: document intent and provide simple confirmation gates for
future Hub actions. No remote shell, no arbitrary command execution.
"""

from __future__ import annotations

from dataclasses import dataclass


# Actions that must never be exposed as free-form remote execution.
FORBIDDEN_CAPABILITIES = frozenset(
    {
        "arbitrary_shell",
        "remote_shell",
        "execute_raw_command",
    }
)

# Future Hub actions that will require explicit operator confirmation.
DANGEROUS_ACTIONS = frozenset(
    {
        "open_application",
        "close_application",
        "write_power_supply",
        "flash_device",
        "erase_device",
    }
)


@dataclass(frozen=True)
class ActionPermission:
    """Result of a permission / confirmation check."""

    allowed: bool
    requires_confirmation: bool
    reason: str


def evaluate_action(
    action: str,
    *,
    confirmed: bool = False,
    granted_permissions: set[str] | None = None,
) -> ActionPermission:
    """Evaluate whether a Hub/integration action may proceed.

    This is a stub policy engine. Real auth/roles come later.
    """
    granted = granted_permissions or set()

    if action in FORBIDDEN_CAPABILITIES:
        return ActionPermission(
            allowed=False,
            requires_confirmation=False,
            reason="Arbitrary command execution is permanently forbidden.",
        )

    if action in DANGEROUS_ACTIONS:
        if action not in granted and "*" not in granted:
            return ActionPermission(
                allowed=False,
                requires_confirmation=True,
                reason=f"Permission not granted for action '{action}'.",
            )
        if not confirmed:
            return ActionPermission(
                allowed=False,
                requires_confirmation=True,
                reason=f"Action '{action}' requires explicit confirmation.",
            )

    return ActionPermission(
        allowed=True,
        requires_confirmation=action in DANGEROUS_ACTIONS,
        reason="ok",
    )
