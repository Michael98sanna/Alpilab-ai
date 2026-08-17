"""Shared session state mutation helpers for realtime V1.1."""

from __future__ import annotations

import re
from typing import Any

from app.realtime.payloads import AssistantStatus, DiagnosticTestPayload

_MEASUREMENT_NUM = re.compile(r"-?\d+(?:\.\d+)?")


class StateUpdateRejected(Exception):
    """Raised when the server refuses a client state mutation."""

    def __init__(self, reason: str, *, request_type: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.request_type = request_type


def evaluate_measurement(value: str) -> tuple[str, str]:
    """
    Derive formatted measurement and status from raw input.

    Rules mirror the approved mock UI:
    - numeric 0 → FAILED
    - numeric > 0 → PASSED
    - otherwise → INVALID
    """
    trimmed = value.strip()
    if not trimmed:
        raise StateUpdateRejected("measurement value required", request_type="diagnostic_update")

    match = _MEASUREMENT_NUM.search(trimmed)
    if not match:
        raise StateUpdateRejected("invalid measurement value", request_type="diagnostic_update")

    num = float(match.group())
    if num == 0:
        status = "FAILED"
    elif num > 0:
        status = "PASSED"
    else:
        status = "INVALID"

    formatted = trimmed if "V" in trimmed.upper() else f"{trimmed} V"
    return formatted, status


def apply_diagnostic_update(
    diagnostics: list[DiagnosticTestPayload],
    test_id: str,
    value: str,
) -> tuple[DiagnosticTestPayload, dict[str, Any]]:
    """Update one diagnostic test and return the test plus change payload."""
    formatted, status = evaluate_measurement(value)
    for test in diagnostics:
        if test.id == test_id:
            test.value = formatted
            test.status = status
            return test, {
                "diagnostic_test": {
                    "id": test.id,
                    "name": test.name,
                    "value": test.value,
                    "status": test.status,
                }
            }
    raise StateUpdateRejected("diagnostic test not found", request_type="diagnostic_update")


def apply_diagnosis_pause(paused: bool) -> dict[str, Any]:
    """Build repair_context changes for pause/resume."""
    if paused:
        return {
            "repair_context": {
                "status": "paused",
                "diagnosis_label": "Diagnosis paused",
            }
        }
    return {
        "repair_context": {
            "status": "active",
            "diagnosis_label": "Diagnosis in progress",
        }
    }


def apply_repair_context_update(
    *,
    device: str | None = None,
    issue: str | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    changes: dict[str, Any] = {"repair_context": {}}
    ctx = changes["repair_context"]
    if device is not None:
        ctx["device"] = device.strip() or None
    if issue is not None:
        ctx["issue"] = issue.strip() or None
    if label is not None:
        ctx["label"] = label.strip() or None
    if not ctx:
        raise StateUpdateRejected(
            "repair_context_update requires at least one field",
            request_type="repair_context_update",
        )
    return changes


def apply_assistant_status_change(status: AssistantStatus) -> dict[str, Any]:
    return {"assistant_status": status}
