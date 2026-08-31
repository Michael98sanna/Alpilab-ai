"""Circuit breaker for AI provider resilience."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker for AI providers."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_sec: int = 60,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout_sec)
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: datetime | None = None

    def record_failure(self) -> None:
        """Record a provider failure."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(UTC)

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def record_success(self) -> None:
        """Reset the circuit after a successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def is_available(self) -> bool:
        """Return whether the circuit accepts new requests."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time is None:
                return False
            if datetime.now(UTC) - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        return True
