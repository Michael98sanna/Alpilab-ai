"""Controlled Windows application configuration models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowsApplicationConfig:
    """Local trusted configuration for a registered Windows application."""

    app_id: str
    name: str
    executable: str
    executable_path: str
    enabled: bool = True
    dry_run: bool = True

    @property
    def allowed(self) -> bool:
        return self.enabled
