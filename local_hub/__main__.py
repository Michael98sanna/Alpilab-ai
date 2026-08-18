"""Start the Alpilab Local Hub from the command line."""

from __future__ import annotations

import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path


def _write_startup_log(text: str) -> None:
    """Minimal crash/startup breadcrumb. Never log env or credentials."""
    candidates = [
        Path.home() / ".alpilab" / "logs" / "startup.log",
    ]
    try:
        from local_hub.paths import log_dir

        candidates.insert(0, log_dir() / "startup.log")
    except Exception:
        pass
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "startup.log")
    for path in candidates:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(text)
            return
        except OSError:
            continue


def main() -> None:
    from local_hub.launcher import main as hub_main

    hub_main()


if __name__ == "__main__":
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        _write_startup_log(f"{stamp} startup frozen={bool(getattr(sys, 'frozen', False))}\n")
        main()
    except Exception:
        _write_startup_log(f"{stamp} crash\n{traceback.format_exc()}\n")
        raise
