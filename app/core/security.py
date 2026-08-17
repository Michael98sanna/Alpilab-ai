"""Security helpers and policy flags for future Hub / hardware actions."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class ActionPolicy:
    """Describes whether an action may proceed and if confirmation is required."""

    allowed: bool
    requires_confirmation: bool
    reason: str


# Actions that must never run without explicit future permission + confirmation.
DANGEROUS_HUB_ACTIONS = frozenset(
    {
        "open_application",
        "close_application",
        "capture_microscope",
        "capture_thermal_camera",
        "read_multimeter",
        "read_power_supply",
    }
)


def evaluate_hub_action(
    action_name: str,
    *,
    confirmed: bool = False,
    settings: Settings | None = None,
) -> ActionPolicy:
    """Evaluate whether a Hub action is allowed under current safety policy.

    This phase never executes real Windows/hardware commands.
    """
    cfg = settings or get_settings()

    if action_name not in DANGEROUS_HUB_ACTIONS and action_name != "get_pc_status":
        return ActionPolicy(
            allowed=False,
            requires_confirmation=False,
            reason=f"Unknown Hub action: {action_name}",
        )

    if action_name == "get_pc_status":
        return ActionPolicy(
            allowed=True,
            requires_confirmation=False,
            reason="Status queries are read-only.",
        )

    if not cfg.allow_dangerous_hub_actions:
        return ActionPolicy(
            allowed=False,
            requires_confirmation=True,
            reason=(
                "Dangerous Hub actions are disabled. "
                "They are mock-only in this phase and must never run arbitrary commands."
            ),
        )

    if cfg.require_confirmation_for_dangerous_actions and not confirmed:
        return ActionPolicy(
            allowed=False,
            requires_confirmation=True,
            reason="Explicit confirmation is required before this Hub action.",
        )

    return ActionPolicy(
        allowed=True,
        requires_confirmation=False,
        reason="Action permitted under current policy (still mock execution only).",
    )
