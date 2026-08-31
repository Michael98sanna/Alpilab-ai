"""Tests for audit logging and RBAC (Priority 3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.models.database import Base
from app.security.audit_log import AuditLogger
from app.security.models import AuditLogModel, UserModel, UserRole  # noqa: F401
from app.security.rbac import ActionRiskLevel, RBACManager


@pytest.fixture
def db_session(tmp_path: Path) -> Session:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'audit.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = factory()
    try:
        yield db
    finally:
        db.close()


def test_log_action(db_session: Session) -> None:
    logger = AuditLogger(db_session)

    logger.log_action(
        user_id="tech-1",
        action_type="TOOL_EXECUTE",
        tool_id="windows.3utools.open",
        status="SUCCESS",
        risk_level="MEDIUM",
    )

    audit = logger.get_user_audit("tech-1")
    assert len(audit) == 1
    assert audit[0]["action_type"] == "TOOL_EXECUTE"


def test_session_audit_history(db_session: Session) -> None:
    logger = AuditLogger(db_session)
    logger.log_action(
        user_id="tech-1",
        session_id="repair-001",
        action_type="CHAT_MESSAGE",
        status="SUCCESS",
    )
    logger.log_action(
        user_id="tech-1",
        session_id="repair-001",
        action_type="TOOL_EXECUTE",
        tool_id="demo.safe_test",
        status="SUCCESS",
        risk_level="MEDIUM",
    )

    history = logger.get_session_audit("repair-001")
    assert len(history) == 2
    assert history[0]["action_type"] == "CHAT_MESSAGE"
    assert history[1]["tool_id"] == "demo.safe_test"


def test_rbac_technician_cannot_high_risk() -> None:
    user = UserModel(id="t1", username="tech", role=UserRole.TECHNICIAN)
    perm = RBACManager.check_permission(user, ActionRiskLevel.HIGH)
    assert not perm.allowed
    assert perm.reason == "Insufficiente permesso"


def test_rbac_supervisor_high_risk_requires_confirmation() -> None:
    user = UserModel(id="s1", username="super", role=UserRole.SUPERVISOR)
    perm = RBACManager.check_permission(user, ActionRiskLevel.HIGH)
    assert perm.allowed
    assert perm.requires_confirmation is True


def test_rbac_admin_can_everything() -> None:
    user = UserModel(id="a1", username="admin", role=UserRole.ADMIN)
    perm = RBACManager.check_permission(user, ActionRiskLevel.HIGH)
    assert perm.allowed
    assert perm.requires_confirmation is False


def test_rbac_inactive_user_denied() -> None:
    user = UserModel(
        id="a1",
        username="admin",
        role=UserRole.ADMIN,
        is_active=False,
    )
    perm = RBACManager.check_permission(user, ActionRiskLevel.LOW)
    assert not perm.allowed


def test_audit_middleware_logs_api_request(db_session: Session, monkeypatch) -> None:
    monkeypatch.setenv("ALPILAB_AUDIT_HTTP", "1")
    logged: list[str] = []

    class _RecordingAuditLogger(AuditLogger):
        def log_action(self, user_id, action_type, **kwargs):
            logged.append(action_type)
            return super().log_action(user_id, action_type, **kwargs)

    monkeypatch.setattr(
        "app.security.audit_middleware.AuditLogger",
        _RecordingAuditLogger,
    )
    monkeypatch.setattr(
        "app.security.audit_middleware.SessionLocal",
        lambda: db_session,
    )
    monkeypatch.setattr(db_session, "close", lambda: None)

    client = TestClient(app)
    response = client.get(
        "/api/v1/realtime/status",
        headers={"X-User-ID": "tech-1"},
    )

    assert response.status_code == 200
    assert any("GET /api/v1/realtime/status" in entry for entry in logged)
