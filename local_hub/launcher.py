"""Run FastAPI + SQLite + mDNS + optional PC Agent + embedded desktop UI."""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import uvicorn

from app.hub.discovery import DEFAULT_HUB_NAME, HubAdvertiser
from local_hub.paths import is_frozen, log_dir, sqlite_path
from local_hub.user_config import load_hub_config

logger = logging.getLogger("alpilab.local_hub")


def _configure_local_env(host: str, port: int, session_id: str) -> None:
    db = sqlite_path()
    os.environ.setdefault("ALPILAB_SESSION_STORE", "sqlite")
    os.environ.setdefault("ALPILAB_SQLITE_PATH", str(db))
    os.environ.setdefault("ALPILAB_DEFAULT_SESSION", session_id)
    os.environ.setdefault("HOST", host)
    os.environ.setdefault("PORT", str(port))
    os.environ.setdefault("ALPILAB_WS_URL", f"ws://127.0.0.1:{port}")
    os.environ.setdefault("ALPILAB_SESSION_ID", session_id)
    os.environ.setdefault("ALPILAB_CAP_WINDOWS_APPS", "true")
    os.environ.setdefault(
        "ALPILAB_WINDOWS_APPS_CONFIG",
        str(Path.home() / ".alpilab" / "windows_apps.json"),
    )
    os.environ.setdefault(
        "ALPILAB_IDENTITY_PATH",
        str(Path.home() / ".alpilab" / "agent_identity.json"),
    )


def _ensure_windows_apps_file() -> None:
    path = Path.home() / ".alpilab" / "windows_apps.json"
    if path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    from pc_agent.windows_apps.discover import discover_3utools_path

    found = discover_3utools_path()
    payload = {
        "windows_apps": {
            "3utools": {
                "enabled": True,
                "executable": "3uTools.exe",
                "executable_path": found or "",
                "dry_run": True,
            }
        }
    }
    import json

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if found:
        logger.info("3uTools path saved to local config")
    else:
        logger.warning(
            "3uTools.exe not found in known Program Files locations. "
            "Edit %%USERPROFILE%%\\.alpilab\\windows_apps.json"
        )


def _start_pc_agent() -> subprocess.Popen | None:
    if os.getenv("ALPILAB_HUB_START_AGENT", "true").strip().lower() not in {
        "1",
        "true",
        "yes",
    }:
        return None
    env = os.environ.copy()
    logger.info("Starting PC Agent")
    if is_frozen():
        return subprocess.Popen([sys.executable, "--agent"], env=env)  # noqa: S603
    return subprocess.Popen([sys.executable, "-m", "pc_agent"], env=env)  # noqa: S603


def _open_desktop(url: str) -> None:
    """Embedded WebView — never opens an external browser."""
    try:
        import webview
    except ImportError:
        logger.warning(
            "pywebview not installed. Hub is running at %s — "
            "install requirements-desktop.txt for the native window.",
            url,
        )
        return
    logger.info("Opening embedded WebView at %s (not Chrome)", url)
    webview.create_window(
        "ALPILAB AI",
        url,
        width=1280,
        height=800,
        min_size=(800, 600),
    )
    webview.start()


def _run_agent_mode() -> None:
    from pc_agent.__main__ import main as agent_main

    agent_main()


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--agent" in argv:
        argv = [a for a in argv if a != "--agent"]
        _run_agent_mode()
        return

    parser = argparse.ArgumentParser(description="Alpilab Local Hub")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-ui", action="store_true")
    parser.add_argument("--no-agent", action="store_true")
    parser.add_argument("--no-mdns", action="store_true")
    parser.add_argument("--name", default=None)
    args = parser.parse_args(argv)

    cfg = load_hub_config()
    host = args.host or str(cfg.get("host") or "0.0.0.0")
    port = int(args.port or cfg.get("port") or 8000)
    name = args.name or str(cfg.get("hub_name") or DEFAULT_HUB_NAME)
    session_id = str(cfg.get("default_session_id") or "repair-001")

    log_path = log_dir() / "hub.log"
    logging.basicConfig(
        level=logging.INFO,
        format="[ALPILAB-HUB] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )
    _configure_local_env(host, port, session_id)
    _ensure_windows_apps_file()
    if args.no_agent or not cfg.get("start_pc_agent", True):
        os.environ["ALPILAB_HUB_START_AGENT"] = "false"

    advertiser = HubAdvertiser(port=port, name=name, lan_ip="127.0.0.1")
    # Advertise the LAN address, keep Windows UI on loopback.
    from app.hub.discovery import detect_lan_ip

    advertiser.lan_ip = detect_lan_ip()
    if not args.no_mdns and cfg.get("start_mdns", True):
        advertiser.start()

    config = uvicorn.Config(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
        lifespan="on",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 15
    while not getattr(server, "started", False) and time.time() < deadline:
        time.sleep(0.1)

    logger.info("Local Hub listening on http://127.0.0.1:%s", port)
    logger.info("LAN URL: %s", advertiser.lan_url)
    logger.info("Default session: %s", session_id)
    logger.info("SQLite: %s", sqlite_path())
    logger.info("User data: %s", Path.home() / ".alpilab")

    agent_proc = _start_pc_agent()
    ui_url = f"http://127.0.0.1:{port}/"

    try:
        if args.no_ui or not cfg.get("start_ui", True):
            logger.info("UI disabled — press Ctrl+C to stop")
            while thread.is_alive():
                time.sleep(0.5)
        else:
            _open_desktop(ui_url)
            server.should_exit = True
    finally:
        if agent_proc and agent_proc.poll() is None:
            agent_proc.terminate()
        advertiser.stop()
        server.should_exit = True


if __name__ == "__main__":
    main()
