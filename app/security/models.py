"""SQLAlchemy ORM models for RBAC and audit logging."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum as SQLEnum, Integer, String

from app.models.database import Base


class UserRole(str, Enum):
    """Laboratory user roles."""

    TECHNICIAN = "technician"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class UserModel(Base):
    """
    RBAC user record.

    Uses ``security_users`` to avoid colliding with the legacy ``users`` table
    in ``SQLiteSessionStore`` (JSON payload schema).
    """

    __tablename__ = "security_users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    role = Column(
        SQLEnum(UserRole, native_enum=False, length=32),
        default=UserRole.TECHNICIAN,
        nullable=False,
    )
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)


class AuditLogModel(Base):
    """Append-only audit trail for security-sensitive actions."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=True, index=True)
    session_id = Column(String, nullable=True, index=True)
    action_type = Column(String, nullable=False)
    tool_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="SUCCESS")
    risk_level = Column(String, nullable=False, default="LOW")
    action_metadata = Column(JSON, nullable=False, default=dict)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
