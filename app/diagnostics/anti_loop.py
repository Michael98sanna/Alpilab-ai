"""Anti-loop detection for diagnostic recommendations."""

from datetime import datetime, timedelta, timezone

from app.diagnostics.models import DiagnosticTestRecord
from app.schemas.enums import DiagnosticTestStatus


class RepeatedRecommendationDetector:
    """Detects when the same test is recommended too often."""

    def __init__(self, window_seconds: int = 300, max_repeats: int = 2) -> None:
        self._window = timedelta(seconds=window_seconds)
        self._max_repeats = max_repeats
        self._history: dict[str, list[datetime]] = {}

    def record_recommendation(self, repair_session_id: str, test_name: str) -> None:
        key = f"{repair_session_id}:{test_name}"
        now = datetime.now(timezone.utc)
        entries = self._history.setdefault(key, [])
        entries.append(now)
        self._history[key] = [
            ts for ts in entries if now - ts <= self._window
        ]

    def is_repeated(self, repair_session_id: str, test_name: str) -> bool:
        key = f"{repair_session_id}:{test_name}"
        return len(self._history.get(key, [])) >= self._max_repeats


def should_recommend_test(record: DiagnosticTestRecord, force: bool = False) -> bool:
    """
    Return whether a diagnostic test should be recommended.

    Valid completed tests are not re-proposed unless forced or retries allow.
    """
    if force:
        return True

    if record.status in {
        DiagnosticTestStatus.PASSED,
        DiagnosticTestStatus.FAILED,
        DiagnosticTestStatus.SKIPPED,
    }:
        if record.evidence is not None and record.status != DiagnosticTestStatus.INVALID:
            return False

    if record.status == DiagnosticTestStatus.INVALID:
        return record.retry_count < record.max_retries

    return record.status in {
        DiagnosticTestStatus.PENDING,
        DiagnosticTestStatus.IN_PROGRESS,
    }
