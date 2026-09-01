"""Dataclass schemas for iPhone panic log parsing and analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PanicLogMetadata:
    bug_type: str
    timestamp: str
    os_version: str
    incident_id: str
    model_code: str
    build_version: str
    process_name: str | None = None
    bundle_id: str | None = None
    app_version: str | None = None


@dataclass
class PanicLogPayload:
    panic_string: str
    process_by_pid: dict[str, Any] = field(default_factory=dict)
    binary_images: list[Any] = field(default_factory=list)
    memory_status: Any | None = None
    raw_content: str = ""


@dataclass
class PanicLogDocument:
    metadata: PanicLogMetadata
    payload: PanicLogPayload
    file_hash: str
    parsed_at: datetime


@dataclass
class RuleMatch:
    rule_id: str
    rule_name: str
    matched: bool
    confidence: float
    component: str | None
    error_code: str | None
    severity: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisFindings:
    panic_type: str
    panic_signature: str | None
    rule_matches: list[RuleMatch]
    dominant_component: str | None
    estimated_severity: str
    estimated_confidence: float
    raw_data: dict[str, Any] = field(default_factory=dict)


def to_dict(obj: Any) -> dict[str, Any]:
    """Convert dataclass (nested) to JSON-serializable dict."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj
