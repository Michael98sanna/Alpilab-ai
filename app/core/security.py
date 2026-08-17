"""Security helpers for future privileged / hardware actions.

No arbitrary shell execution is allowed. Dangerous actions must be confirmed.
"""

from __future__ import annotations


class ConfirmationRequiredError(PermissionError):
    """Raised when a privileged action is requested without explicit confirmation."""


def require_confirmation(confirmed: bool, action: str) -> None:
    """Gate potentially dangerous Hub / hardware actions.

    Callers must pass ``confirmed=True`` only after an explicit human approval
    in the UI. This is a hard requirement for future PC-control features.
    """
    if not confirmed:
        raise ConfirmationRequiredError(
            f"Azione '{action}' richiede conferma esplicita dell'operatore."
        )
