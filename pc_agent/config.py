"""Centralized configuration for PC Agent."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class AgentConfig:
    ws_url: str
    session_id: str
    agent_name: str
    platform: str
    agent_version: str
    heartbeat_interval_sec: float
    reconnect_base_delay_sec: float
    reconnect_max_delay_sec: float
    reconnect_max_attempts: int
    log_level: str
    identity_path: str
    capabilities_windows_apps: bool
    capabilities_alpilab_check: bool
    capabilities_microscope: bool
    capabilities_thermal_camera: bool
    capabilities_multimeter: bool
    capabilities_power_supply: bool
    capabilities_safe_test: bool

    @classmethod
    def from_env(cls) -> "AgentConfig":
        ws_base = os.getenv("ALPILAB_WS_URL", "ws://127.0.0.1:8000").rstrip("/")
        session_id = os.getenv("ALPILAB_SESSION_ID", "repair-001")
        default_dir = os.path.join(os.path.expanduser("~"), ".alpilab")
        return cls(
            ws_url=ws_base,
            session_id=session_id,
            agent_name=os.getenv("ALPILAB_AGENT_NAME", "ALPILAB-PC"),
            platform=os.getenv("ALPILAB_AGENT_PLATFORM", "windows"),
            agent_version=os.getenv("ALPILAB_AGENT_VERSION", "0.3.0"),
            heartbeat_interval_sec=_env_float("ALPILAB_HEARTBEAT_INTERVAL", 25.0),
            reconnect_base_delay_sec=_env_float("ALPILAB_RECONNECT_BASE_DELAY", 1.0),
            reconnect_max_delay_sec=_env_float("ALPILAB_RECONNECT_MAX_DELAY", 32.0),
            reconnect_max_attempts=_env_int("ALPILAB_RECONNECT_MAX_ATTEMPTS", 8),
            log_level=os.getenv("ALPILAB_LOG_LEVEL", "INFO"),
            identity_path=os.getenv(
                "ALPILAB_IDENTITY_PATH",
                os.path.join(default_dir, "agent_identity.json"),
            ),
            capabilities_windows_apps=os.getenv("ALPILAB_CAP_WINDOWS_APPS", "true").lower()
            in {"1", "true", "yes"},
            capabilities_alpilab_check=os.getenv("ALPILAB_CAP_ALPILAB_CHECK", "false").lower()
            in {"1", "true", "yes"},
            capabilities_microscope=os.getenv("ALPILAB_CAP_MICROSCOPE", "false").lower()
            in {"1", "true", "yes"},
            capabilities_thermal_camera=os.getenv(
                "ALPILAB_CAP_THERMAL_CAMERA", "false"
            ).lower()
            in {"1", "true", "yes"},
            capabilities_multimeter=os.getenv("ALPILAB_CAP_MULTIMETER", "false").lower()
            in {"1", "true", "yes"},
            capabilities_power_supply=os.getenv("ALPILAB_CAP_POWER_SUPPLY", "false").lower()
            in {"1", "true", "yes"},
            capabilities_safe_test=os.getenv("ALPILAB_CAP_SAFE_TEST", "true").lower()
            in {"1", "true", "yes"},
        )

    def websocket_url(self, agent_id: str) -> str:
        base = self.ws_url.replace("http://", "ws://").replace("https://", "wss://")
        return (
            f"{base}/ws/agent/{self.session_id}"
            f"?agent_id={agent_id}"
        )
