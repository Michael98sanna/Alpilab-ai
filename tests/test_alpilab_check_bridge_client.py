"""Tests for PC Agent Alpilab Check bridge client (Milestone 1 / V1 contract)."""

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


def _v1_ok(tool: str, data: dict, request_id: str = "req-1") -> str:
    return json.dumps(
        {
            "protocol_version": "v1",
            "tool": tool,
            "request_id": request_id,
            "success": True,
            "data": data,
            "error": None,
        }
    )


def test_health_uses_v1_path_and_token_header(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout):  # noqa: ANN001
        assert timeout == 1.5
        assert req.full_url == "http://127.0.0.1:57421/v1/health"
        assert req.get_method() == "GET"
        assert req.get_header("X-alpilab-token") == "test-secret"
        return _FakeResponse(
            _v1_ok("alpilab_check.health", {"status": "ok", "protocol_version": "v1"})
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    data = _client().health()
    assert data["status"] == "ok"
    assert data["protocol_version"] == "v1"


def test_protocol_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout: _FakeResponse(
            json.dumps(
                {
                    "protocol_version": "v2",
                    "tool": "alpilab_check.health",
                    "request_id": "health-get",
                    "success": True,
                    "data": {"status": "ok"},
                    "error": None,
                }
            )
        ),
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


def _assert_v1_tool_post(req, *, tool: str, arguments: dict) -> None:  # noqa: ANN001
    assert req.full_url == "http://127.0.0.1:57421/v1"
    assert req.get_method() == "POST"
    assert req.get_header("X-alpilab-token") == "test-secret"
    body = json.loads(req.data.decode("utf-8"))
    assert body["protocol_version"] == "v1"
    assert body["tool"] == tool
    assert isinstance(body["request_id"], str) and body["request_id"]
    assert body["arguments"] == arguments


def test_search_products_posts_v1_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_ids: list[str] = []

    def fake_urlopen(req, timeout):  # noqa: ANN001
        _assert_v1_tool_post(
            req,
            tool="alpilab_check.search_products",
            arguments={"query": "iPhone", "limit": 20},
        )
        body = json.loads(req.data.decode("utf-8"))
        seen_ids.append(body["request_id"])
        return _FakeResponse(
            _v1_ok(
                "alpilab_check.search_products",
                {"items": [{"id": "p1", "name": "iPhone"}]},
                request_id=body["request_id"],
            )
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    data = _client().search_products("iPhone")
    assert data["items"][0]["name"] == "iPhone"
    assert len(seen_ids) == 1


def test_get_product_posts_v1_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout):  # noqa: ANN001
        _assert_v1_tool_post(
            req,
            tool="alpilab_check.get_product",
            arguments={"id": "prod-1"},
        )
        body = json.loads(req.data.decode("utf-8"))
        assert "product_id" not in body["arguments"]
        return _FakeResponse(
            _v1_ok("alpilab_check.get_product", {"id": "prod-1", "name": "Battery"})
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    data = _client().get_product("prod-1")
    assert data["id"] == "prod-1"


def test_get_product_bridge_payload_uses_id_not_product_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bridge V1 requires arguments.id; internal API still uses product_id."""
    captured: list[dict] = []

    def fake_urlopen(req, timeout):  # noqa: ANN001
        body = json.loads(req.data.decode("utf-8"))
        captured.append(body)
        return _FakeResponse(
            _v1_ok(
                "alpilab_check.get_product",
                {
                    "id": "item-0",
                    "name": "Apple||iphone 3",
                    "services": [{"name": "Schermo", "price": 89}],
                },
                request_id=body["request_id"],
            )
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    data = _client().get_product("item-0")
    assert captured[0]["tool"] == "alpilab_check.get_product"
    assert captured[0]["arguments"] == {"id": "item-0"}
    assert "product_id" not in captured[0]["arguments"]
    assert data["services"][0]["name"] == "Schermo"


def test_search_invoices_posts_v1_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout):  # noqa: ANN001
        _assert_v1_tool_post(
            req,
            tool="alpilab_check.search_invoices",
            arguments={"query": "SERVICE", "limit": 10},
        )
        return _FakeResponse(
            _v1_ok("alpilab_check.search_invoices", {"items": [{"id": "i1"}]})
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    data = _client().search_invoices("SERVICE", limit=10)
    assert data["items"][0]["id"] == "i1"


def test_get_invoice_posts_v1_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout):  # noqa: ANN001
        _assert_v1_tool_post(
            req,
            tool="alpilab_check.get_invoice",
            arguments={"invoice_id": "inv-42"},
        )
        return _FakeResponse(
            _v1_ok("alpilab_check.get_invoice", {"id": "inv-42", "total": 10.0})
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    data = _client().get_invoice("inv-42")
    assert data["total"] == 10.0


def test_request_ids_are_unique_across_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    ids: list[str] = []

    def fake_urlopen(req, timeout):  # noqa: ANN001
        body = json.loads(req.data.decode("utf-8"))
        ids.append(body["request_id"])
        return _FakeResponse(
            _v1_ok(body["tool"], {"ok": True}, request_id=body["request_id"])
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    _client().search_products("a")
    _client().get_product("p1")
    assert len(ids) == 2
    assert ids[0] != ids[1]
