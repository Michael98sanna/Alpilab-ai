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

logger = logging.getLogger("alpilab.local_hub")


def _configure_local_env(host: str, port: int) -> None:
    os.environ.setdefault("ALPILAB_SESSION_STORE", "sqlite")
    os.environ.setdefault("ALPILAB_SQLITE_PATH", str(Path("data") / "alpilab.db"))
    os.environ.setdefault("ALPILAB_DEFAULT_SESSION", "repair-001")
    os.environ.setdefault("HOST", host)
    os.environ.setdefault("PORT", str(port))
    os.environ.setdefault("ALPILAB_WS_URL", f"ws://127.0.0.1:{port}")
    os.environ.setdefault("ALPILAB_SESSION_ID", "repair-001")
    os.environ.setdefault("ALPILAB_CAP_WINDOWS_APPS", "true")


def _start_pc_agent() -> subprocess.Popen | None:
    if os.getenv("ALPILAB_HUB_START_AGENT", "true").strip().lower() not in {
        "1",
        "true",
        "yes",
    }:
        return None
    env = os.environ.copy()
    logger.info("Starting PC Agent subprocess")
    return subprocess.Popen(  # noqa: S603
        [sys.executable, "-m", "pc_agent"],
        env=env,
    )


def _open_desktop(url: str) -> None:
    """Embedded WebView — never opens an external browser."""
    try:
        import webview
    except ImportError:
        logger.warning(
            "pywebview not installed. Hub is running at %s — "
            "install pywebview for ALPILAB AI.exe-style window (not Chrome).",
            url,
        )
        return
    webview.create_window(
        "ALPILAB AI",
        url,
        width=1280,
        height=800,
        min_size=(800, 600),
    )
    webview.start()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Alpilab Local Hub")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-ui", action="store_true", help="Hub only, no desktop window")
    parser.add_argument("--no-agent", action="store_true", help="Do not spawn PC Agent")
    parser.add_argument("--no-mdns", action="store_true", help="Do not advertise on LAN")
    parser.add_argument("--name", default=DEFAULT_HUB_NAME)
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="[ALPILAB-HUB] %(message)s",
    )
    _configure_local_env(args.host, args.port)
    if args.no_agent:
        os.environ["ALPILAB_HUB_START_AGENT"] = "false"

    advertiser = HubAdvertiser(port=args.port, name=args.name)
    if not args.no_mdns:
        advertiser.start()

    config = uvicorn.Config(
        "app.main:app",
        host=args.host,
        port=args.port,
        log_level="info",
        lifespan="on",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 15
    while not getattr(server, "started", False) and time.time() < deadline:
        time.sleep(0.1)

    logger.info("Local Hub listening on http://127.0.0.1:%s", args.port)
    logger.info("LAN URL: %s", advertiser.lan_url)
    logger.info("Default session: repair-001")

    agent_proc = _start_pc_agent()
    ui_url = f"http://127.0.0.1:{args.port}/"

    try:
        if args.no_ui:
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
