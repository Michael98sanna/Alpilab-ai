"""mDNS / Bonjour advertisement for Alpilab Local Hub."""

from __future__ import annotations

import logging
import socket
from typing import Any

logger = logging.getLogger("alpilab.discovery")

SERVICE_TYPE = "_alpilab._tcp.local."
DEFAULT_HUB_NAME = "Alpilab Negozio"


def detect_lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class HubAdvertiser:
    """Advertise the Local Hub on the LAN. No-op if zeroconf is missing."""

    def __init__(
        self,
        *,
        port: int = 8000,
        name: str = DEFAULT_HUB_NAME,
        lan_ip: str | None = None,
    ) -> None:
        self.port = port
        self.name = name
        self.lan_ip = lan_ip or detect_lan_ip()
        self._zeroconf: Any = None
        self._info: Any = None

    @property
    def lan_url(self) -> str:
        return f"http://{self.lan_ip}:{self.port}"

    def start(self) -> bool:
        try:
            from zeroconf import ServiceInfo, Zeroconf
        except ImportError:
            logger.warning("zeroconf not installed — LAN discovery disabled")
            return False

        self._zeroconf = Zeroconf()
        service_name = f"{self.name}.{SERVICE_TYPE}"
        self._info = ServiceInfo(
            SERVICE_TYPE,
            service_name,
            addresses=[socket.inet_aton(self.lan_ip)],
            port=self.port,
            properties={
                b"name": self.name.encode("utf-8"),
                b"path": b"/",
                b"session": b"repair-001",
            },
            server=f"{self.name.replace(' ', '-').lower()}.local.",
        )
        self._zeroconf.register_service(self._info)
        logger.info("mDNS advertised %s at %s", service_name, self.lan_url)
        return True

    def stop(self) -> None:
        if self._zeroconf and self._info:
            try:
                self._zeroconf.unregister_service(self._info)
            except Exception:
                logger.debug("mDNS unregister failed", exc_info=True)
            self._zeroconf.close()
        self._zeroconf = None
        self._info = None
