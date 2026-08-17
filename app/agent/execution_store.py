"""In-memory idempotency and pending command tracking for tool execution."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.agent.payloads import ResultEnvelope


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class PendingExecution:
    request_id: str
    command_id: str
    tool_id: str
    agent_id: str
    session_id: str
    future: asyncio.Future[ResultEnvelope]
    created_at: datetime = field(default_factory=_utc_now)


class ToolExecutionStore:
    """Tracks pending and completed tool executions by request_id."""

    def __init__(self, default_timeout_sec: float = 30.0) -> None:
        self.default_timeout_sec = default_timeout_sec
        self._pending: dict[str, PendingExecution] = {}
        self._completed: dict[str, ResultEnvelope] = {}

    def get_completed(self, request_id: str) -> ResultEnvelope | None:
        return self._completed.get(request_id)

    def register_pending(
        self,
        *,
        request_id: str,
        command_id: str,
        tool_id: str,
        agent_id: str,
        session_id: str,
    ) -> asyncio.Future[ResultEnvelope]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        existing = self._completed.get(request_id)
        if existing is not None:
            future: asyncio.Future[ResultEnvelope] = loop.create_future()
            future.set_result(existing)
            return future

        pending = self._pending.get(request_id)
        if pending is not None:
            return pending.future

        future = loop.create_future()
        self._pending[request_id] = PendingExecution(
            request_id=request_id,
            command_id=command_id,
            tool_id=tool_id,
            agent_id=agent_id,
            session_id=session_id,
            future=future,
        )
        return future

    def complete(self, result: ResultEnvelope) -> bool:
        """Store result and resolve waiter. Returns False if duplicate completed."""
        if result.request_id in self._completed:
            return False
        self._completed[result.request_id] = result
        pending = self._pending.pop(result.request_id, None)
        if pending is not None and not pending.future.done():
            pending.future.set_result(result)
        return True

    def fail_pending(self, request_id: str, error: str) -> None:
        pending = self._pending.pop(request_id, None)
        if pending is not None and not pending.future.done():
            pending.future.set_exception(TimeoutError(error))

    def clear(self) -> None:
        self._pending.clear()
        self._completed.clear()


tool_execution_store = ToolExecutionStore()
