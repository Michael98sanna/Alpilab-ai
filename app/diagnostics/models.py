"""Diagnostic evidence and state management."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import DiagnosisConfidence, DiagnosticTestStatus, EvidenceKind


class RecordedEvidence(BaseModel):
    """Structured evidence for a diagnostic test result."""

    value: float | str | None = None
    unit: str | None = None
    source: str | None = None
    tool_id: str | None = None
    recorded_at: datetime | None = None
    notes: str | None = None
    confidence: DiagnosisConfidence | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiagnosticEvidence(BaseModel):
    """Typed evidence linked to a repair session."""

    id: str
    repair_session_id: str
    kind: EvidenceKind
    label: str
    content: str | None = None
    evidence: RecordedEvidence | None = None
    diagnostic_test_id: str | None = None
    created_at: datetime | None = None


class DiagnosticTestRecord(BaseModel):
    """Runtime diagnostic test state managed outside AI prompts."""

    id: str
    repair_session_id: str
    name: str
    status: DiagnosticTestStatus = DiagnosticTestStatus.PENDING
    evidence: RecordedEvidence | None = None
    retry_count: int = 0
    max_retries: int = 3
    last_recommended_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
