"""Realtime layer for Alpilab AI."""

from app.realtime.events import RealtimeEvent, RealtimeEventType

__all__ = ["RealtimeEvent", "RealtimeEventType", "RealtimeSessionManager"]


def __getattr__(name: str):
    # Lazy: importing RealtimeSessionManager at package load breaks PyInstaller
    # collect_submodules (circular import while session_manager is initializing).
    if name == "RealtimeSessionManager":
        from app.realtime.session_manager import RealtimeSessionManager as cls

        return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
