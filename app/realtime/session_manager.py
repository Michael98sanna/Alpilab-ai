"""Realtime session synchronization layer."""

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.realtime.events import RealtimeEvent, RealtimeEventType

RealtimeSubscriber = Callable[[RealtimeEvent], None]


class RealtimeSessionManager:
    """
    Manages realtime event fan-out for repair sessions.

    Future implementations may use WebSocket or equivalent transport.
    This in-memory manager is used for tests and local development.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[RealtimeSubscriber]] = defaultdict(list)
        self._event_log: list[RealtimeEvent] = []

    def subscribe(self, repair_session_id: str, handler: RealtimeSubscriber) -> None:
        self._subscribers[repair_session_id].append(handler)

    def unsubscribe(self, repair_session_id: str, handler: RealtimeSubscriber) -> None:
        handlers = self._subscribers.get(repair_session_id, [])
        self._subscribers[repair_session_id] = [h for h in handlers if h != handler]

    def emit(
        self,
        repair_session_id: str,
        event_type: RealtimeEventType,
        payload: dict[str, Any] | None = None,
        source_client_device_id: str | None = None,
    ) -> RealtimeEvent:
        event = RealtimeEvent(
            id=str(uuid4()),
            repair_session_id=repair_session_id,
            event_type=event_type,
            payload=payload or {},
            emitted_at=datetime.now(timezone.utc),
            source_client_device_id=source_client_device_id,
        )
        self._event_log.append(event)
        for handler in self._subscribers.get(repair_session_id, []):
            handler(event)
        return event

    def events_for_session(self, repair_session_id: str) -> list[RealtimeEvent]:
        return [
            event
            for event in self._event_log
            if event.repair_session_id == repair_session_id
        ]
