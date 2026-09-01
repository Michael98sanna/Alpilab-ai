"""Pydantic schemas for iPhone panic log tool results (Hub)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IPhonePanicCheckResult(BaseModel):
    status: str
    device_id: str | None = None
    device_name: str | None = None
    ios_version: str | None = None
    model: str | None = None
    panic_log_filename: str | None = None
    panic_timestamp: str | float | None = None
    file_hash: str | None = None
    cached: bool = False
    error_message: str | None = None


class IPhonePanicAnalysisResult(BaseModel):
    status: str
    device_id: str | None = None
    device_name: str | None = None
    ios_version: str | None = None
    model: str | None = None
    panic_log_filename: str | None = None
    panic_type: str | None = None
    panic_string: str | None = None
    component: str | None = None
    severity: str | None = None
    confidence: float | None = None
    recommendations: list[str] = Field(default_factory=list)
    raw_findings: list[dict[str, Any]] = Field(default_factory=list)
    cached: bool = False
    error_message: str | None = None
