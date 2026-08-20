"""mDNS / Bonjour advertisement for Alpilab Local Hub."""

from __future__ import annotations

import ipaddress
import logging
import platform
import socket
import struct
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("alpilab.discovery")

SERVICE_TYPE = "_alpilab._tcp.local."
DEFAULT_HUB_NAME = "Alpilab Negozio"

_LOCAL_UI_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", "testclient"})


@dataclass(frozen=True)
class LocalInterface:
    ip: str
    prefix: int
    name: str = ""


def _is_usable_ipv4(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    if not isinstance(addr, ipaddress.IPv4Address):
        return False
    return not (addr.is_loopback or addr.is_link_local or addr.is_multicast)


def _mask_to_prefix(mask: str) -> int:
    try:
        return ipaddress.ip_address(mask).bit_count()
    except ValueError:
        return 24


def _enumerate_posix() -> list[LocalInterface]:
    import fcntl

    interfaces: list[LocalInterface] = []
    for _index, name in socket.if_nameindex():
        if name == "lo":
            continue
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            ifreq = struct.pack("256s", name.encode("utf-8")[:15])
            ip = socket.inet_ntoa(
                fcntl.ioctl(sock.fileno(), 0x8915, ifreq)[20:24]  # SIOCGIFADDR
            )
            mask = socket.inet_ntoa(
                fcntl.ioctl(sock.fileno(), 0x891B, ifreq)[20:24]  # SIOCGIFNETMASK
            )
        except OSError:
            continue
        finally:
            sock.close()
        if _is_usable_ipv4(ip):
            interfaces.append(LocalInterface(ip=ip, prefix=_mask_to_prefix(mask), name=name))
    return interfaces


def _enumerate_windows() -> list[LocalInterface]:
    import json
    import subprocess
    import sys

    script = (
        "Get-NetIPAddress -AddressFamily IPv4 | "
        "Select-Object IPAddress, PrefixLength, InterfaceAlias | "
        "ConvertTo-Json -Compress"
    )
    run_kwargs: dict = {
        "capture_output": True,
        "text": True,
        "timeout": 15,
        "check": False,
    }
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        run_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        run_kwargs["startupinfo"] = startupinfo
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script],
            **run_kwargs,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    rows = payload if isinstance(payload, list) else [payload]

    interfaces: list[LocalInterface] = []
    for item in rows:
        ip = str(item.get("IPAddress", "")).strip()
        try:
            prefix = int(item.get("PrefixLength") or 24)
        except (TypeError, ValueError):
            prefix = 24
        name = str(item.get("InterfaceAlias") or "")
        if _is_usable_ipv4(ip):
            interfaces.append(LocalInterface(ip=ip, prefix=prefix, name=name))
    return interfaces


def _enumerate_local_interfaces() -> list[LocalInterface]:
    system = platform.system()
    if system == "Windows":
        interfaces = _enumerate_windows()
    elif system in {"Linux", "Darwin"}:
        interfaces = _enumerate_posix()
    else:
        interfaces = []

    deduped: dict[str, LocalInterface] = {}
    for iface in interfaces:
        if _is_usable_ipv4(iface.ip):
            deduped[iface.ip] = iface
    return sorted(deduped.values(), key=lambda item: item.ip)


def enumerate_local_ipv4() -> list[str]:
    """Return usable IPv4 addresses on active local interfaces."""
    ips = [iface.ip for iface in _enumerate_local_interfaces() if _is_usable_ipv4(iface.ip)]
    if ips:
        return ips
    fallback = _default_route_ipv4()
    return [fallback] if fallback and _is_usable_ipv4(fallback) else []


def _default_route_ipv4() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def _normalize_remote_host(remote_host: str | None) -> str | None:
    if remote_host is None:
        return None
    host = remote_host.strip()
    if not host or host.lower() in _LOCAL_UI_HOSTS:
        return None
    if host.startswith("::ffff:"):
        host = host.removeprefix("::ffff:")
    return host


def _same_subnet(local_ip: str, prefix: int, remote_host: str) -> bool:
    try:
        network = ipaddress.ip_network(f"{local_ip}/{prefix}", strict=False)
        return ipaddress.ip_address(remote_host) in network
    except ValueError:
        return False


def select_lan_ip(remote_host: str | None = None) -> str:
    """Pick the local IPv4 best suited for the requesting client."""
    interfaces = _enumerate_local_interfaces()
    remote = _normalize_remote_host(remote_host)

    if remote and interfaces:
        matches = [
            iface for iface in interfaces if _same_subnet(iface.ip, iface.prefix, remote)
        ]
        if matches:
            matches.sort(key=lambda item: (item.prefix, item.ip), reverse=True)
            return matches[0].ip

    ips = [iface.ip for iface in interfaces]
    if ips:
        legacy = _default_route_ipv4()
        if legacy in ips:
            return legacy
        return ips[0]

    legacy = _default_route_ipv4()
    return legacy if legacy else "127.0.0.1"


def detect_lan_ip() -> str:
    """Backward-compatible single-IP helper (default-route preference)."""
    return select_lan_ip(None)


class HubAdvertiser:
    """Advertise the Local Hub on the LAN. No-op if zeroconf is missing."""

    def __init__(
        self,
        *,
        port: int = 8000,
        name: str = DEFAULT_HUB_NAME,
        lan_ip: str | None = None,
        lan_ips: list[str] | None = None,
    ) -> None:
        self.port = port
        self.name = name
        self.lan_ips = lan_ips or enumerate_local_ipv4()
        if lan_ip:
            if lan_ip not in self.lan_ips:
                self.lan_ips = [lan_ip, *self.lan_ips]
            self.lan_ip = lan_ip
        else:
            self.lan_ip = self.lan_ips[0] if self.lan_ips else detect_lan_ip()
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

        addresses = [
            socket.inet_aton(ip)
            for ip in self.lan_ips
            if _is_usable_ipv4(ip)
        ]
        if not addresses:
            addresses = [socket.inet_aton(detect_lan_ip())]

        self._zeroconf = Zeroconf()
        service_name = f"{self.name}.{SERVICE_TYPE}"
        self._info = ServiceInfo(
            SERVICE_TYPE,
            service_name,
            addresses=addresses,
            port=self.port,
            properties={
                b"name": self.name.encode("utf-8"),
                b"path": b"/",
                b"session": b"repair-001",
            },
            server=f"{self.name.replace(' ', '-').lower()}.local.",
        )
        self._zeroconf.register_service(self._info)
        logger.info(
            "mDNS advertised %s at %s",
            service_name,
            ", ".join(self.lan_ips),
        )
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
