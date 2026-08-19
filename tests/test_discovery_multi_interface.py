"""V0.5.4 multi-interface discovery tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.hub.discovery import (
    HubAdvertiser,
    LocalInterface,
    enumerate_local_ipv4,
    select_lan_ip,
)
from app.hub.routes import hub_info
from app.main import app


DUAL_INTERFACES = [
    LocalInterface(ip="192.168.0.41", prefix=24, name="Ethernet"),
    LocalInterface(ip="192.168.137.1", prefix=24, name="Hotspot"),
]


@pytest.fixture
def dual_interfaces(monkeypatch):
    monkeypatch.setattr(
        "app.hub.discovery._enumerate_local_interfaces",
        lambda: list(DUAL_INTERFACES),
    )


def test_enumerate_local_ipv4_excludes_loopback_and_apipa(monkeypatch):
    monkeypatch.setattr(
        "app.hub.discovery._enumerate_local_interfaces",
        lambda: [
            LocalInterface(ip="127.0.0.1", prefix=8, name="lo"),
            LocalInterface(ip="169.254.10.2", prefix=16, name="apipa"),
            LocalInterface(ip="192.168.0.41", prefix=24, name="Ethernet"),
            LocalInterface(ip="192.168.137.1", prefix=24, name="Hotspot"),
        ],
    )
    ips = enumerate_local_ipv4()
    assert ips == ["192.168.0.41", "192.168.137.1"]


def test_select_lan_ip_hotspot_client(dual_interfaces, monkeypatch):
    monkeypatch.setattr(
        "app.hub.discovery._default_route_ipv4",
        lambda: "192.168.0.41",
    )
    assert select_lan_ip("192.168.137.56") == "192.168.137.1"


def test_select_lan_ip_ethernet_client(dual_interfaces, monkeypatch):
    monkeypatch.setattr(
        "app.hub.discovery._default_route_ipv4",
        lambda: "192.168.0.41",
    )
    assert select_lan_ip("192.168.0.20") == "192.168.0.41"


def test_select_lan_ip_without_client_prefers_default_route(dual_interfaces, monkeypatch):
    monkeypatch.setattr(
        "app.hub.discovery._default_route_ipv4",
        lambda: "192.168.0.41",
    )
    assert select_lan_ip(None) == "192.168.0.41"
    assert select_lan_ip("127.0.0.1") == "192.168.0.41"


def test_hub_info_request_aware_hotspot(dual_interfaces, monkeypatch):
    monkeypatch.setattr(
        "app.hub.discovery._default_route_ipv4",
        lambda: "192.168.0.41",
    )
    info = hub_info(client_host="192.168.137.56")
    assert info["lan_ip"] == "192.168.137.1"
    assert info["lan_url"] == "http://192.168.137.1:8000"
    assert info["ws_url"] == "ws://192.168.137.1:8000"
    assert info["default_session_id"] == "repair-001"
    assert info["pairing_required"] is True
    assert info["lan_ips"] == ["192.168.0.41", "192.168.137.1"]


def test_hub_info_request_aware_ethernet(dual_interfaces, monkeypatch):
    monkeypatch.setattr(
        "app.hub.discovery._default_route_ipv4",
        lambda: "192.168.0.41",
    )
    info = hub_info(client_host="192.168.0.20")
    assert info["lan_ip"] == "192.168.0.41"
    assert info["lan_url"] == "http://192.168.0.41:8000"


def test_hub_info_endpoint_still_ok(dual_interfaces, monkeypatch):
    monkeypatch.setattr(
        "app.hub.discovery._default_route_ipv4",
        lambda: "192.168.0.41",
    )
    client = TestClient(app)
    res = client.get("/api/v1/hub/info")
    assert res.status_code == 200
    body = res.json()
    assert body["default_session_id"] == "repair-001"
    assert body["lan_ip"] == "192.168.0.41"
    assert body["pairing_required"] is True


def test_mdns_registers_multiple_addresses(dual_interfaces):
    advertiser = HubAdvertiser(port=8000, lan_ips=["192.168.0.41", "192.168.137.1"])
    mock_zc = MagicMock()
    captured: dict = {}

    class FakeServiceInfo:
        def __init__(self, service_type, name, addresses, port, properties, server):
            captured["addresses"] = addresses
            captured["port"] = port

    with patch("zeroconf.Zeroconf", return_value=mock_zc):
        with patch("zeroconf.ServiceInfo", FakeServiceInfo):
            assert advertiser.start() is True

    assert len(captured["addresses"]) == 2
    assert captured["port"] == 8000
