"""API schemas for ALPILAB Brain endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BrainChatRequest(BaseModel):
    card_id: str
    message: str = Field(min_length=1, max_length=8000)


class BrainChatResponse(BaseModel):
    content: str
    provider: str
    model: str
    source: str
    confidence: float
    task_type: str
    diagnosis_type: str | None = None
    similar_cases_count: int = 0
    kb_hits: int = 0
    used_online: bool = False
    latency_ms: int = 0
    low_accuracy_warning: bool = False
    knowledge_entry_id: str | None = None
    kb_mode: str = "disabled"
    strong_match: bool = False
    validation: dict = Field(default_factory=lambda: {
        "performed": False,
        "agreed": None,
        "overridden": False,
    })


class BrainFeedbackRequest(BaseModel):
    feedback: str = Field(pattern="^(confirmed|corrected|rejected)$")
    correction_text: str | None = None
    provider: str | None = None
    pre_confidence: float = 0.0
    knowledge_entry_id: str | None = None
    ai_diagnosis: str | None = None


class BrainOutcomeRequest(BaseModel):
    outcome: str = Field(pattern="^(success|partial|failed)$")
    notes: str | None = None


class BrainFeedbackResponse(BaseModel):
    confirmation_id: str
    status: str = "recorded"


class BrainOutcomeResponse(BaseModel):
    confirmation_id: str
    status: str = "outcome_recorded"


class KBSearchResult(BaseModel):
    id: str
    text: str
    diagnosis: str
    solution: str
    diagnosis_type: str
    device_type: str
    confidence_score: float
    similarity: float
