"""Tests for DiagnosticTest."""

from uuid import uuid4

from app.models import DiagnosticTest, DiagnosticTestStatus


def test_diagnostic_test_defaults(session_id) -> None:
    test = DiagnosticTest(session_id=session_id, name="Battery health")

    assert test.status is DiagnosticTestStatus.PENDING
    assert test.category == "hardware"
    assert test.raw_payload is None


def test_diagnostic_test_keeps_opaque_payload(session_id) -> None:
    payload = {"origin": "future-check-export", "unknown_field": 42}
    test = DiagnosticTest(
        session_id=session_id,
        name="Touch ID",
        category="biometrics",
        status=DiagnosticTestStatus.FAILED,
        result_summary="fail",
        source="alpilab_check",
        raw_payload=payload,
    )

    assert test.raw_payload == payload
    assert test.source == "alpilab_check"


def test_diagnostic_test_session_id_is_required() -> None:
    test = DiagnosticTest(session_id=uuid4(), name="Speaker")
    assert test.name == "Speaker"
