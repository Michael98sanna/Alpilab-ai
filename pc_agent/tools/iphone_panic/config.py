"""Resolve libimobiledevice binary paths for iPhone panic tools."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def find_libimobiledevice_binary(binary_name: str) -> Path | None:
    """Locate idevice_* binaries without depending on external GUI apps."""
    env_dir = os.getenv("ALPILAB_LIBIMOBILEDEVICE_DIR", "").strip()
    search_paths: list[Path] = []
    if env_dir:
        search_paths.append(Path(env_dir))

    home = Path.home()
    search_paths.extend(
        [
            home / "AppData/Local/iDevicePanicLogAnalyzer/app-1.7.4/win-x64",
            Path("C:/Program Files/iTunes"),
            Path("C:/Program Files (x86)/iTunes"),
        ]
    )

    bundled = Path(__file__).resolve().parents[2] / "third_party" / "libimobiledevice" / "win-x64"
    search_paths.append(bundled)

    for search_path in search_paths:
        candidate = search_path / binary_name
        if candidate.is_file():
            return candidate

    which = shutil.which(binary_name)
    if which:
        return Path(which)

    if os.name == "nt":
        result = subprocess.run(
            ["where", binary_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip().splitlines()[0])

    return None
