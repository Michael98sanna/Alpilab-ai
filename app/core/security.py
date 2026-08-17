"""Security primitives used across backend and hub abstractions.

This phase does not implement authentication. It does establish two rules
that future hardware/PC actions must follow:

1. A capability must be explicitly permitted.
2. Potentially dangerous actions require an explicit confirmation flag.
   Absence of confirmation is a refusal, not an implicit yes.
"""

from __future__ import annotations

from dataclasses import dataclass


class SecurityError(Exception):
    """Base class for security-related refusals."""


class ConfirmationRequiredError(SecurityError):
    """Raised when a dangerous action is requested without confirmation."""

    def __init__(self, action: str) -> None:
        self.action = action
        super().__init__(
            f"Azione '{action}' richiede conferma esplicita. "
            "Nessuna operazione è stata eseguita."
        )


class PermissionDeniedError(SecurityError):
    """Raised when the caller is not allowed to perform a capability."""

    def __init__(self, capability: str) -> None:
        self.capability = capability
        super().__init__(
            f"Permesso mancante per la capability '{capability}'. "
            "Nessuna operazione è stata eseguita."
        )


# Capabilities that read state and do not change the PC or hardware.
SAFE_READ_CAPABILITIES = frozenset(
    {
        "get_pc_status",
        "capture_microscope",
        "capture_thermal_camera",
        "read_multimeter",
        "read_power_supply",
    }
)

# Capabilities that can interrupt work or launch software on the bench PC.
DANGEROUS_CAPABILITIES = frozenset(
    {
        "open_application",
        "close_application",
    }
)


@dataclass(frozen=True)
class PermissionContext:
    """Who is asking, and which Hub capabilities they may use.

    Authentication is not implemented yet. Callers construct this explicitly
    so future auth can populate it without changing Hub method signatures.
    """

    actor: str = "anonymous"
    allowed_capabilities: frozenset[str] = SAFE_READ_CAPABILITIES

    def allows(self, capability: str) -> bool:
        return capability in self.allowed_capabilities


def require_permission(context: PermissionContext, capability: str) -> None:
    if not context.allows(capability):
        raise PermissionDeniedError(capability)


def require_explicit_confirmation(confirmed: bool, action: str) -> None:
    """Refuse unless the caller set confirmed=True.

    Confirmation must be an explicit boolean. Missing/false is a denial.
    """
    if confirmed is not True:
        raise ConfirmationRequiredError(action)
