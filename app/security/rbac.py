"""Role-based access control for laboratory users."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.security.models import UserModel, UserRole


class ActionRiskLevel(str, Enum):
    """RBAC risk tiers (distinct from ``app.schemas.enums.ActionRiskLevel``)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionPermission(BaseModel):
    """Authorization decision for a role + risk combination."""

    allowed: bool
    requires_confirmation: bool = False
    reason: str | None = None


class RBACManager:
    """Role-based access control matrix."""

    PERMISSIONS: dict[UserRole, dict[ActionRiskLevel, ActionPermission]] = {
        UserRole.TECHNICIAN: {
            ActionRiskLevel.LOW: ActionPermission(allowed=True),
            ActionRiskLevel.MEDIUM: ActionPermission(allowed=True),
            ActionRiskLevel.HIGH: ActionPermission(
                allowed=False,
                reason="Insufficiente permesso",
            ),
        },
        UserRole.SUPERVISOR: {
            ActionRiskLevel.LOW: ActionPermission(allowed=True),
            ActionRiskLevel.MEDIUM: ActionPermission(allowed=True),
            ActionRiskLevel.HIGH: ActionPermission(
                allowed=True,
                requires_confirmation=True,
            ),
        },
        UserRole.ADMIN: {
            ActionRiskLevel.LOW: ActionPermission(allowed=True),
            ActionRiskLevel.MEDIUM: ActionPermission(allowed=True),
            ActionRiskLevel.HIGH: ActionPermission(allowed=True),
        },
    }

    @staticmethod
    def check_permission(user: UserModel, risk_level: ActionRiskLevel) -> ActionPermission:
        """Return whether ``user`` may perform an action at ``risk_level``."""
        is_active = getattr(user, "is_active", True)
        if is_active is False:
            return ActionPermission(
                allowed=False,
                reason="Utente disattivato",
            )

        role_permissions = RBACManager.PERMISSIONS.get(user.role)
        if role_permissions is None:
            return ActionPermission(
                allowed=False,
                reason="Ruolo non riconosciuto",
            )

        permission = role_permissions.get(risk_level)
        if permission is None:
            return ActionPermission(
                allowed=False,
                reason="Livello di rischio non supportato",
            )
        return permission
