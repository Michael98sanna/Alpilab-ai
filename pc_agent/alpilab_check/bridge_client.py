"""HTTP client for local Alpilab Check bridge (protocol v1)."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

ALPILAB_CHECK_UNAVAILABLE = "ALPILAB_CHECK_UNAVAILABLE"
ALPILAB_CHECK_TIMEOUT = "ALPILAB_CHECK_TIMEOUT"
ALPILAB_CHECK_PROTOCOL_MISMATCH = "ALPILAB_CHECK_PROTOCOL_MISMATCH"
ALPILAB_CHECK_UNAUTHORIZED = "ALPILAB_CHECK_UNAUTHORIZED"
ALPILAB_CHECK_INVALID_RESPONSE = "ALPILAB_CHECK_INVALID_RESPONSE"
ALPILAB_CHECK_UPSTREAM_ERROR = "ALPILAB_CHECK_UPSTREAM_ERROR"

_BRIDGE_PROTOCOL_VERSION = "v1"
_BRIDGE_BASE_URL = "http://127.0.0.1:57421"
_MIN_TIMEOUT_SEC = 0.5
_MAX_TIMEOUT_SEC = 30.0
_DEFAULT_TIMEOUT_SEC = 4.0
_SECRET_ENV = "ALPILAB_CHECK_BRIDGE_SECRET"
_SECRET_PATH_ENV = "ALPILAB_CHECK_BRIDGE_SECRET_PATH"
_SECRET_HEADER = "X-Alpilab-Check-Secret"
_PROTOCOL_HEADER = "X-Alpilab-Check-Protocol-Version"

logger = logging.getLogger("alpilab.pc_agent")


class AlpilabCheckBridgeError(Exception):
    """Typed bridge error with stable code for upper layers."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


@dataclass(frozen=True)
class BridgeClientConfig:
    """Configuration for localhost bridge calls."""

    secret: str
    timeout_sec: float = _DEFAULT_TIMEOUT_SEC


def _parse_timeout(raw: str | None) -> float:
    if not raw:
        return _DEFAULT_TIMEOUT_SEC
    try:
        value = float(raw)
    except ValueError:
        return _DEFAULT_TIMEOUT_SEC
    return min(max(value, _MIN_TIMEOUT_SEC), _MAX_TIMEOUT_SEC)


def _load_secret() -> str:
    secret = os.getenv(_SECRET_ENV, "").strip()
    if secret:
        return secret
    secret_path = os.getenv(_SECRET_PATH_ENV, "").strip()
    if not secret_path:
        raise AlpilabCheckBridgeError(
            ALPILAB_CHECK_UNAUTHORIZED,
            "bridge secret not configured",
        )
    try:
        loaded = Path(secret_path).read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise AlpilabCheckBridgeError(
            ALPILAB_CHECK_UNAUTHORIZED,
            "bridge secret not configured",
        ) from exc
    if not loaded:
        raise AlpilabCheckBridgeError(
            ALPILAB_CHECK_UNAUTHORIZED,
            "bridge secret not configured",
        )
    return loaded


def _assert_localhost_url(url: str) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip("[]").lower()
    if parsed.scheme != "http" or host not in {"127.0.0.1", "localhost"}:
        raise AlpilabCheckBridgeError(
            ALPILAB_CHECK_UNAVAILABLE,
            "bridge URL must be localhost only",
        )
    if parsed.port != 57421:
        raise AlpilabCheckBridgeError(
            ALPILAB_CHECK_UNAVAILABLE,
            "bridge URL must use port 57421",
        )


class AlpilabCheckBridgeClient:
    """Client for Alpilab Check local bridge, pinned to localhost v1."""

    def __init__(self, config: BridgeClientConfig) -> None:
        _assert_localhost_url(_BRIDGE_BASE_URL)
        self._base_url = _BRIDGE_BASE_URL
        self._secret = config.secret
        self._timeout_sec = config.timeout_sec

    @classmethod
    def from_env(cls) -> "AlpilabCheckBridgeClient":
        secret = _load_secret()
        timeout = _parse_timeout(os.getenv("ALPILAB_CHECK_BRIDGE_TIMEOUT_SEC"))
        return cls(BridgeClientConfig(secret=secret, timeout_sec=timeout))

    def health(self) -> dict[str, Any]:
        payload = self._request_json("GET", "/health")
        protocol = payload.get("protocol_version")
        if protocol != _BRIDGE_PROTOCOL_VERSION:
            raise AlpilabCheckBridgeError(
                ALPILAB_CHECK_PROTOCOL_MISMATCH,
                f"unsupported protocol_version={protocol!r}",
            )
        return payload

    def search_products(self, query: str, limit: int = 20) -> dict[str, Any]:
        return self._request_json(
            "POST",
            "/search_products",
            {"query": query, "limit": limit},
        )

    def get_product(self, product_id: str) -> dict[str, Any]:
        return self._request_json("POST", "/get_product", {"product_id": product_id})

    def search_invoices(self, query: str, limit: int = 20) -> dict[str, Any]:
        return self._request_json(
            "POST",
            "/search_invoices",
            {"query": query, "limit": limit},
        )

    def get_invoice(self, invoice_id: str) -> dict[str, Any]:
        return self._request_json("POST", "/get_invoice", {"invoice_id": invoice_id})

    def _request_json(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        data = None
        headers = {
            "Accept": "application/json",
            _SECRET_HEADER: self._secret,
            _PROTOCOL_HEADER: _BRIDGE_PROTOCOL_VERSION,
        }
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url=url, method=method, data=data, headers=headers)
        try:
            with request.urlopen(req, timeout=self._timeout_sec) as response:  # noqa: S310
                raw = response.read().decode("utf-8", errors="replace")
        except TimeoutError as exc:
            logger.warning("Alpilab Check bridge timeout method=%s path=%s", method, path)
            raise AlpilabCheckBridgeError(ALPILAB_CHECK_TIMEOUT) from exc
        except error.HTTPError as exc:
            if exc.code in {401, 403}:
                logger.warning("Alpilab Check bridge unauthorized method=%s path=%s", method, path)
                raise AlpilabCheckBridgeError(ALPILAB_CHECK_UNAUTHORIZED) from exc
            logger.warning(
                "Alpilab Check bridge upstream error code=%s method=%s path=%s",
                exc.code,
                method,
                path,
            )
            raise AlpilabCheckBridgeError(ALPILAB_CHECK_UPSTREAM_ERROR) from exc
        except error.URLError as exc:
            reason = str(exc.reason).lower() if getattr(exc, "reason", None) else ""
            if "timed out" in reason or "timeout" in reason:
                logger.warning("Alpilab Check bridge timeout method=%s path=%s", method, path)
                raise AlpilabCheckBridgeError(ALPILAB_CHECK_TIMEOUT) from exc
            logger.warning("Alpilab Check bridge unavailable method=%s path=%s", method, path)
            raise AlpilabCheckBridgeError(ALPILAB_CHECK_UNAVAILABLE) from exc
        except OSError as exc:
            logger.warning("Alpilab Check bridge unavailable method=%s path=%s", method, path)
            raise AlpilabCheckBridgeError(ALPILAB_CHECK_UNAVAILABLE) from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AlpilabCheckBridgeError(ALPILAB_CHECK_INVALID_RESPONSE) from exc
        if not isinstance(parsed, dict):
            raise AlpilabCheckBridgeError(ALPILAB_CHECK_INVALID_RESPONSE)
        return parsed
