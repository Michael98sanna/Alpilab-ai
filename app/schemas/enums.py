"""Shared enums used across repair data schemas."""

from enum import Enum


class RepairSessionStatus(str, Enum):
    """Lifecycle status of a repair session."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_PARTS = "waiting_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiagnosticTestStatus(str, Enum):
    """Execution status of a diagnostic test."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DiagnosisConfidence(str, Enum):
    """Confidence level for a diagnosis."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONFIRMED = "confirmed"


class RepairResultStatus(str, Enum):
    """Outcome of a repair attempt."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"


class ImageAttachmentKind(str, Enum):
    """Category of an attached image."""

    BEFORE = "before"
    AFTER = "after"
    MICROSCOPE = "microscope"
    THERMAL = "thermal"
    BOARDVIEW = "boardview"
    OTHER = "other"
