"""Mock Alpilab Hub — no real Windows / hardware interaction."""

from __future__ import annotations

from hub.interface import AlpilabHub, HubActionResult, PcStatus

# Allow-listed application ids for the future real Hub (documentation only).
KNOWN_APPLICATIONS = frozenset(
    {
        "3utools",
        "borneo",
        "zxw",
        "alpilab_check",
    }
)


class MockAlpilabHub(AlpilabHub):
    """In-memory Hub stub. Clearly identified as MOCK; no side effects."""

    name = "alpilab_hub_mock"

    def is_available(self) -> bool:
        return True

    def get_pc_status(self) -> PcStatus:
        return PcStatus(
            online=True,
            hostname="mock-lab-pc",
            os_name="Windows (mock)",
            details={"mock": True},
        )

    def open_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        return self._app_action("open_application", app_id, confirmed=confirmed)

    def close_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        return self._app_action("close_application", app_id, confirmed=confirmed)

    def capture_microscope(self) -> HubActionResult:
        return HubActionResult(
            success=True,
            action="capture_microscope",
            message="[MOCK] Cattura microscopio non eseguita (placeholder).",
            data={"image_path": None},
        )

    def capture_thermal_camera(self) -> HubActionResult:
        return HubActionResult(
            success=True,
            action="capture_thermal_camera",
            message="[MOCK] Cattura termocamera non eseguita (placeholder).",
            data={"image_path": None},
        )

    def read_multimeter(self) -> HubActionResult:
        return HubActionResult(
            success=True,
            action="read_multimeter",
            message="[MOCK] Lettura multimetro non eseguita (placeholder).",
            data={"value": None, "unit": None},
        )

    def read_power_supply(self) -> HubActionResult:
        return HubActionResult(
            success=True,
            action="read_power_supply",
            message="[MOCK] Lettura alimentatore non eseguita (placeholder).",
            data={"voltage": None, "current": None},
        )

    def _app_action(
        self, action: str, app_id: str, *, confirmed: bool
    ) -> HubActionResult:
        if app_id not in KNOWN_APPLICATIONS:
            return HubActionResult(
                success=False,
                action=action,
                message=(
                    f"[MOCK] Applicazione '{app_id}' non in allow-list. "
                    f"Consentite: {sorted(KNOWN_APPLICATIONS)}"
                ),
                data={"app_id": app_id},
                requires_confirmation=True,
                confirmed=confirmed,
            )

        # Future dangerous actions will require explicit confirmation.
        if not confirmed:
            return HubActionResult(
                success=False,
                action=action,
                message=(
                    f"[MOCK] Conferma obbligatoria per {action} su '{app_id}'. "
                    "Nessuna azione reale eseguita."
                ),
                data={"app_id": app_id},
                requires_confirmation=True,
                confirmed=False,
            )

        return HubActionResult(
            success=True,
            action=action,
            message=f"[MOCK] {action} simulato per '{app_id}' (nessun processo avviato).",
            data={"app_id": app_id},
            requires_confirmation=True,
            confirmed=True,
        )
