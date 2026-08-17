"""Diagnostic state machine with anti-loop guarantees."""

from datetime import datetime, timezone
from uuid import uuid4

from app.diagnostics.anti_loop import RepeatedRecommendationDetector, should_recommend_test
from app.diagnostics.models import DiagnosticEvidence, DiagnosticTestRecord, RecordedEvidence
from app.schemas.enums import DiagnosticTestStatus, EvidenceKind
from app.schemas.session_events import SessionEvent, SessionEventType


class DiagnosticStateManager:
    """Manages diagnostic test lifecycle and evidence outside AI prompts."""

    def __init__(
        self,
        max_retries: int = 3,
        recommendation_detector: RepeatedRecommendationDetector | None = None,
    ) -> None:
        self._tests: dict[str, DiagnosticTestRecord] = {}
        self._evidence: list[DiagnosticEvidence] = []
        self._session_events: list[SessionEvent] = []
        self._max_retries = max_retries
        self._detector = recommendation_detector or RepeatedRecommendationDetector()

    def register_test(self, repair_session_id: str, name: str) -> DiagnosticTestRecord:
        record = DiagnosticTestRecord(
            id=str(uuid4()),
            repair_session_id=repair_session_id,
            name=name,
            max_retries=self._max_retries,
        )
        self._tests[record.id] = record
        return record

    def get_test(self, test_id: str) -> DiagnosticTestRecord | None:
        return self._tests.get(test_id)

    def start_test(self, test_id: str) -> DiagnosticTestRecord:
        record = self._tests[test_id]
        record.status = DiagnosticTestStatus.IN_PROGRESS
        return record

    def complete_test(
        self,
        test_id: str,
        status: DiagnosticTestStatus,
        evidence: RecordedEvidence | None = None,
    ) -> DiagnosticTestRecord:
        record = self._tests[test_id]
        record.status = status
        record.evidence = evidence
        self._session_events.append(
            SessionEvent(
                id=str(uuid4()),
                repair_session_id=record.repair_session_id,
                event_type=SessionEventType.DIAGNOSTIC_TEST_COMPLETED,
                payload={"test_id": test_id, "status": status.value},
                created_at=datetime.now(timezone.utc),
            )
        )
        return record

    def recommend_next_test(self, repair_session_id: str, test_name: str) -> bool:
        record = self._find_test_by_name(repair_session_id, test_name)
        if record is None:
            record = self.register_test(repair_session_id, test_name)

        if not should_recommend_test(record):
            return False

        if self._detector.is_repeated(repair_session_id, test_name):
            return False

        self._detector.record_recommendation(repair_session_id, test_name)
        record.last_recommended_at = datetime.now(timezone.utc)
        return True

    def add_evidence(
        self,
        repair_session_id: str,
        kind: EvidenceKind,
        label: str,
        content: str | None = None,
        evidence: RecordedEvidence | None = None,
        diagnostic_test_id: str | None = None,
    ) -> DiagnosticEvidence:
        item = DiagnosticEvidence(
            id=str(uuid4()),
            repair_session_id=repair_session_id,
            kind=kind,
            label=label,
            content=content,
            evidence=evidence,
            diagnostic_test_id=diagnostic_test_id,
            created_at=datetime.now(timezone.utc),
        )
        self._evidence.append(item)
        return item

    def session_events(self) -> list[SessionEvent]:
        return list(self._session_events)

    def _find_test_by_name(
        self, repair_session_id: str, test_name: str
    ) -> DiagnosticTestRecord | None:
        for record in self._tests.values():
            if (
                record.repair_session_id == repair_session_id
                and record.name == test_name
            ):
                return record
        return None
