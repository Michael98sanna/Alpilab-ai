"""Tests for PC Agent Alpilab Check bridge client (Milestone 1)."""

from __future__ import annotations

import json
import logging
import socket
from urllib import error

import pytest

from pc_agent.alpilab_check.bridge_client import (
    ALPILAB_CHECK_INVALID_RESPONSE,
    ALPILAB_CHECK_PROTOCOL_MISMATCH,
    ALPILAB_CHECK_TIMEOUT,
    ALPILAB_CHECK_UNAUTHORIZED,
    ALPILAB_CHECK_UNAVAILABLE,
    AlpilabCheckBridgeClient,
    AlpilabCheckBridgeError,
    BridgeClientConfig,
    _assert_localhost_url,
)


class _FakeResponse:
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload.encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001
        return False


def _client(secret: str = "test-secret") -> AlpilabCheckBridgeClient:
    return AlpilabCheckBridgeClient(BridgeClientConfig(secret=secret, timeout_sec=1.5))


def test_health_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout):  # noqa: ANN001
        assert timeout == 1.5
        assert req.full_url.endswith("/health")
        return _FakeResponse(json.dumps({"status": "ok", "protocol_version": "v1"}))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    data = _client().health()
    assert data["status"] == "ok"
    assert data["protocol_version"] == "v1"


def test_protocol_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout: _FakeResponse(json.dumps({"status": "ok", "protocol_version": "v2"})),
    )
    with pytest.raises(AlpilabCheckBridgeError) as exc:
        _client().health()
    assert exc.value.code == ALPILAB_CHECK_PROTOCOL_MISMATCH


def test_bridge_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout: (_ for _ in ()).throw(error.URLError("connection refused")),
    )
    with pytest.raises(AlpilabCheckBridgeError) as exc:
        _client().health()
    assert exc.value.code == ALPILAB_CHECK_UNAVAILABLE


def test_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout: (_ for _ in ()).throw(socket.timeout("timed out")),
    )
    with pytest.raises(AlpilabCheckBridgeError) as exc:
        _client().search_products("iphone")
    assert exc.value.code == ALPILAB_CHECK_TIMEOUT


def test_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout):  # noqa: ANN001
        raise error.HTTPError(req.full_url, 401, "unauthorized", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(AlpilabCheckBridgeError) as exc:
        _client().get_product("prod-1")
    assert exc.value.code == ALPILAB_CHECK_UNAUTHORIZED


def test_malformed_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout: _FakeResponse("not-json"))
    with pytest.raises(AlpilabCheckBridgeError) as exc:
        _client().search_invoices("2026")
    assert exc.value.code == ALPILAB_CHECK_INVALID_RESPONSE


def test_localhost_enforcement_rejects_lan_url() -> None:
    with pytest.raises(AlpilabCheckBridgeError) as exc:
        _assert_localhost_url("http://192.168.0.50:57421")
    assert exc.value.code == ALPILAB_CHECK_UNAVAILABLE


def test_secret_not_in_logs(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    secret = "super-secret-token-123"
    caplog.set_level(logging.WARNING, logger="alpilab.pc_agent")

    def fake_urlopen(req, timeout):  # noqa: ANN001
        raise error.HTTPError(req.full_url, 403, "forbidden", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(AlpilabCheckBridgeError):
        _client(secret=secret).get_invoice("inv-42")
    assert secret not in caplog.text
