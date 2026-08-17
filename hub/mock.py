"""MOCK Alpilab Hub — no real Windows or hardware interaction."""

from __future__ import annotations

from app.core.security import evaluate_hub_action
from hub.base import (
    AlpilabHub,
    HubActionResult,
    HubCapability,
    HubPCStatus,
)


class MockAlpilabHub(AlpilabHub):
    """Deterministic mock Hub for tests and local architecture validation."""

    name = "alpilab_hub_mock"

    def __init__(self, *, available: bool = True) -> None:
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def get_pc_status(self) -> HubPCStatus:
        return HubPCStatus(
            online=self._available,
            hostname="mock-lab-pc",
            os_name="Windows (mock)",
            capabilities=[c.value for c in HubCapability],
            metadata={"mock": True},
        )

    def open_application(
        self, application_id: str, *, confirmed: bool = False
    ) -> HubActionResult:
        return self._mock_action(
            HubCapability.OPEN_APPLICATION.value,
            confirmed=confirmed,
            data={"application_id": application_id},
            message=f"[MOCK] open_application({application_id!r}) — non eseguito.",
        )

    def close_application(
        self, application_id: str, *, confirmed: bool = False
    ) -> HubActionResult:
        return self._mock_action(
            HubCapability.CLOSE_APPLICATION.value,
            confirmed=confirmed,
            data={"application_id": application_id},
            message=f"[MOCK] close_application({application_id!r}) — non eseguito.",
        )

    def capture_microscope(self, *, confirmed: bool = False) -> HubActionResult:
        return self._mock_action(
            HubCapability.CAPTURE_MICROSCOPE.value,
            confirmed=confirmed,
            data={"image_path": None},
            message="[MOCK] capture_microscope — nessuna cattura reale.",
        )

    def capture_thermal_camera(self, *, confirmed: bool = False) -> HubActionResult:
        return self._mock_action(
            HubCapability.CAPTURE_THERMAL_CAMERA.value,
            confirmed=confirmed,
            data={"image_path": None},
            message="[MOCK] capture_thermal_camera — nessuna cattura reale.",
        )

    def read_multimeter(self, *, confirmed: bool = False) -> HubActionResult:
        return self._mock_action(
            HubCapability.READ_MULTIMETER.value,
            confirmed=confirmed,
            data={"reading": None, "unit": None},
            message="[MOCK] read_multimeter — nessuna lettura reale.",
        )

    def read_power_supply(self, *, confirmed: bool = False) -> HubActionResult:
        return self._mock_action(
            HubCapability.READ_POWER_SUPPLY.value,
            confirmed=confirmed,
            data={"voltage": None, "current": None},
            message="[MOCK] read_power_supply — nessuna lettura reale.",
        )

    def _mock_action(
        self,
        action: str,
        *,
        confirmed: bool,
        data: dict,
        message: str,
    ) -> HubActionResult:
        if not self._available:
            return HubActionResult(
                success=False,
                action=action,
                message="[MOCK] Hub non disponibile.",
                data={},
                is_mock=True,
            )

        policy = evaluate_hub_action(action, confirmed=confirmed)
        if not policy.allowed:
            return HubActionResult(
                success=False,
                action=action,
                message=f"[MOCK] Azione bloccata: {policy.reason}",
                data=data,
                is_mock=True,
                requires_confirmation=policy.requires_confirmation,
            )

        return HubActionResult(
            success=True,
            action=action,
            message=message,
            data={**data, "mock": True},
            is_mock=True,
            requires_confirmation=False,
        )
