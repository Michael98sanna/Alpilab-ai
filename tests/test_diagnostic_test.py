"""Tests for DiagnosticTest model."""

from app.models.repair import DiagnosticTest, DiagnosticTestStatus


def test_diagnostic_test_defaults():
    test = DiagnosticTest(name="Display pixel test")
    assert test.status == DiagnosticTestStatus.PENDING
    assert test.id
    assert test.performed_at is None


def test_diagnostic_test_completed():
    test = DiagnosticTest(
        name="Speaker test",
        status=DiagnosticTestStatus.PASSED,
        expected_result="audio chiaro",
        actual_result="audio chiaro",
        procedure="Riproduci tono di prova",
    )
    assert test.status == DiagnosticTestStatus.PASSED
    assert test.expected_result == test.actual_result
