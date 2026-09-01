"""Pydantic schemas for diagnostic card API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DiagnosticCardCreate(BaseModel):
    device_id: str = Field(..., min_length=1)
    device_name: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)


class DiagnosticCardUpdate(BaseModel):
    current_symptom: str | None = None
    hypothesis: str | None = None
    confidence: float | None = None
    diagnostic_stage: str | None = None
    user_notes: str | None = None


class DiagnosticMessageCreate(BaseModel):
    role: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class DiagnosticCardArchive(BaseModel):
    outcome: str = Field(..., min_length=1)
    final_diagnosis: str = Field(..., min_length=1)
    solution: str = Field(..., min_length=1)


class DiagnosticMessageSchema(BaseModel):
    role: str
    content: str
    timestamp: str


class DiagnosticCardSummary(BaseModel):
    device: str
    status: str
    started: str
    updated: str
    current_symptom: str | None
    hypothesis: str | None
    confidence: float
    messages_count: int
    diagnostic_stage: str


class DiagnosticCardResponse(BaseModel):
    id: str
    device_id: str
    device_name: str
    status: str
    current_symptom: str | None
    hypothesis: str | None
    confidence: float
    created_at: datetime
    updated_at: datetime
    diagnostic_stage: str
