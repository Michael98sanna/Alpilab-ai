"""Single-instance guard for the Local Hub desktop process."""

from __future__ import annotations

import atexit
import socket
from typing import Final

_LOCK_HOST: Final[str] = "127.0.0.1"
_LOCK_PORT: Final[int] = 45879
_LOCK_SOCKET: socket.socket | None = None


def acquire_single_instance_lock() -> bool:
    """Acquire a process lock; return False when another instance exists."""
    global _LOCK_SOCKET  # noqa: PLW0603
    if _LOCK_SOCKET is not None:
        return True
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((_LOCK_HOST, _LOCK_PORT))
        sock.listen(1)
    except OSError:
        sock.close()
        return False
    _LOCK_SOCKET = sock
    atexit.register(release_single_instance_lock)
    return True


def release_single_instance_lock() -> None:
    """Release the process lock, if held."""
    global _LOCK_SOCKET  # noqa: PLW0603
    if _LOCK_SOCKET is None:
        return
    try:
        _LOCK_SOCKET.close()
    finally:
        _LOCK_SOCKET = None
