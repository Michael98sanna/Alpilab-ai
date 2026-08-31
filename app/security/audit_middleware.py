"""HTTP middleware for automatic API audit logging."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from starlette.responses import Response

from app.models.database import SessionLocal
from app.security.audit_log import AuditLogError, AuditLogger

logger = logging.getLogger(__name__)


def _audit_http_enabled() -> bool:
    return os.getenv("ALPILAB_AUDIT_HTTP", "1").strip().lower() not in {
        "0",
        "false",
        "no",
    }


def register_audit_logging_middleware(app: FastAPI) -> None:
    """Log successful and failed requests under ``/api/v1``."""

    @app.middleware("http")
    async def audit_logging_middleware(request: Request, call_next) -> Response:
        if not _audit_http_enabled():
            return await call_next(request)

        response = await call_next(request)

        if not request.url.path.startswith("/api/v1"):
            return response

        db = SessionLocal()
        audit = AuditLogger(db)
        try:
            user_id = request.headers.get("X-User-ID")
            audit.log_action(
                user_id=user_id,
                action_type=f"{request.method} {request.url.path}",
                status="SUCCESS" if response.status_code < 400 else "FAILURE",
                risk_level="LOW",
                metadata={
                    "status_code": response.status_code,
                    "client_host": request.client.host if request.client else None,
                },
            )
        except AuditLogError:
            logger.warning("Audit log skipped for %s", request.url.path)
        finally:
            db.close()

        return response
