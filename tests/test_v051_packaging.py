"""V0.5.1 packaging, auth, discovery, storage tests — no real LAN IPs required."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pairing.service import PairingService
from app.realtime.session_manager import realtime_manager
from app.security.client_auth import (
    authorize_session_client,
    ClientAuthError,
    is_local_hub_ui,
    pairing_enforced,
)
from app.session.factory import reset_session_store_cache
from app.session.sqlite_store import SQLiteSessionStore
from local_hub.paths import ensure_user_layout, is_frozen
from local_hub.user_config import DEFAULT_CONFIG, load_hub_config
from pc_agent.windows_apps.config import DEFAULT_CONFIG_PATH
from pc_agent.windows_apps.discover import KNOWN_3UTOOLS_NAME, discover_3utools_path


@pytest.fixture(autouse=True)
def _reset():
    yield
    reset_session_store_cache()
    realtime_manager._persistence_store = None


def test_user_layout(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("local_hub.paths.user_dir", lambda: tmp_path / ".alpilab")
    layout = ensure_user_layout()
    assert layout["data"].is_dir()
    assert layout["logs"].is_dir()
    assert layout["storage"].is_dir()


def test_load_hub_config_creates_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("local_hub.paths.user_dir", lambda: tmp_path / ".alpilab")
    cfg = load_hub_config()
    assert cfg["hub_name"] == DEFAULT_CONFIG["hub_name"]
    assert (tmp_path / ".alpilab" / "config.json").is_file()


def test_discover_3utools_known_paths_only(tmp_path, monkeypatch) -> None:
    from pc_agent.windows_apps import discover as disc

    monkeypatch.setattr(disc, "_windows_drive", lambda: tmp_path)
    assert discover_3utools_path() is None
    target = tmp_path / "Program Files" / "3uTools" / KNOWN_3UTOOLS_NAME
    target.parent.mkdir(parents=True)
    target.write_text("stub")
    found = discover_3utools_path()
    assert found is not None
    assert found.endswith(KNOWN_3UTOOLS_NAME)


def test_discover_ignores_other_exe(tmp_path, monkeypatch) -> None:
    from pc_agent.windows_apps import discover as disc

    monkeypatch.setattr(disc, "_windows_drive", lambda: tmp_path)
    other = tmp_path / "Program Files" / "3uTools" / "malware.exe"
    other.parent.mkdir(parents=True)
    other.write_text("nope")
    assert discover_3utools_path() is None


def test_loopback_pc_ui_skips_pairing() -> None:
    assert is_local_hub_ui("127.0.0.1", "pc")
    assert is_local_hub_ui("::ffff:127.0.0.1", "pc")
    assert is_local_hub_ui("::1", "pc")
    assert not is_local_hub_ui("127.0.0.1", "phone")
    assert not is_local_hub_ui("192.168.1.10", "pc")


def test_pairing_token_required(tmp_path) -> None:
    store = SQLiteSessionStore(tmp_path / "p.db")
    svc = PairingService(store)
    started = svc.start()
    result = svc.complete(
        started["code"],
        client_id="phone-1",
        client_type="phone",
        platform="android",
        device_name="Pixel",
    )
    assert svc.is_authorized("phone-1", result["token"])
    assert not svc.is_authorized("phone-1", None)
    assert not svc.is_authorized("phone-1", "wrong-token")
    svc.revoke("phone-1")
    assert not svc.is_authorized("phone-1", result["token"])


def test_authorize_session_memory_store_allows_tests() -> None:
    reset_session_store_cache()
    assert pairing_enforced() is False
    authorize_session_client(
        host="10.0.0.2",
        device_id="phone-x",
        device_type="phone",
        pairing_token=None,
    )


def test_authorize_phone_requires_token_when_enforced(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPILAB_REQUIRE_CLIENT_PAIRING", "true")
    monkeypatch.setenv("ALPILAB_SESSION_STORE", "sqlite")
    monkeypatch.setenv("ALPILAB_SQLITE_PATH", str(tmp_path / "auth.db"))
    reset_session_store_cache()
    with pytest.raises(ClientAuthError) as exc:
        authorize_session_client(
            host="10.0.0.8",
            device_id="phone-x",
            device_type="phone",
            pairing_token=None,
        )
    assert exc.value.code == "PAIRING_REQUIRED"
    monkeypatch.delenv("ALPILAB_REQUIRE_CLIENT_PAIRING", raising=False)
    monkeypatch.delenv("ALPILAB_SESSION_STORE", raising=False)
    reset_session_store_cache()


def test_photo_storage(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.storage.photos.storage_dir", lambda: tmp_path)
    from app.storage.photos import list_session_photos, save_session_photo

    saved = save_session_photo("repair-001", "pic.jpg", b"jpeg-bytes")
    assert saved["bytes"] == 10
    assert saved["filename"].endswith(".jpg")
    names = list_session_photos("repair-001")
    assert len(names) == 1


def test_is_frozen_false_in_tests() -> None:
    assert is_frozen() is False


def test_hub_info_still_ok() -> None:
    client = TestClient(app)
    res = client.get("/api/v1/hub/info")
    assert res.status_code == 200
    assert res.json()["default_session_id"] == "repair-001"


def test_spec_paths_survive_packaging_cwd() -> None:
    """PyInstaller runs the spec with CWD=packaging/; relative local_hub/ would miss."""
    repo = Path(__file__).resolve().parent.parent
    spec = (repo / "packaging" / "alpilab.spec").read_text(encoding="utf-8")
    assert "SPECPATH" in spec
    assert "local_hub" in spec
    packaging = repo / "packaging"
    assert not (packaging / "local_hub" / "__main__.py").exists()
    assert (repo / "local_hub" / "__main__.py").is_file()
    assert (repo / "frontend" / "dist" / "index.html").is_file()
    assert (repo / "pc_agent" / "windows_apps.json.example").is_file()


def test_user_data_independent_of_cwd(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    layout_root = tmp_path / "home" / ".alpilab"
    monkeypatch.setattr("local_hub.paths.user_dir", lambda: layout_root)
    layout = ensure_user_layout()
    assert layout["root"] == layout_root
    assert tmp_path.joinpath("data").exists() is False
    assert ".alpilab" in DEFAULT_CONFIG_PATH.replace("\\", "/")
    assert DEFAULT_CONFIG_PATH.endswith("windows_apps.json")


def test_startup_log_source_does_not_record_secrets() -> None:
    src = (Path(__file__).resolve().parent.parent / "local_hub" / "__main__.py").read_text(
        encoding="utf-8"
    )
    assert "startup.log" in src
    assert "os.environ" not in src
    assert "pairing" not in src.lower()
    lowered = src.lower()
    assert "authorization" not in lowered
    assert "password" not in lowered
