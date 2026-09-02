"""Pydantic schemas for ALPILAB Brain AI."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    DIAGNOSIS = "diagnosis"
    KNOWLEDGE_SEARCH = "knowledge_search"
    EXPLANATION = "explanation"
    CODE_ANALYSIS = "code_analysis"
    REASONING = "reasoning"
    QUICK_ANSWER = "quick_answer"


class ResponseSource(str, Enum):
    LOCAL_KB = "local_kb"
    HYBRID = "hybrid"
    ONLINE = "online"


class LLMResponse(BaseModel):
    provider: str
    model: str
    content: str
    reasoning: str | None = None
    citations: list[str] = Field(default_factory=list)
    confidence: float = 0.75
    tokens_used: int = 0
    latency_ms: int = 0
    cost_estimate: float = 0.0


class KnowledgeCase(BaseModel):
    id: str
    text: str
    diagnosis_type: str
    device_type: str
    diagnosis: str
    solution: str
    confidence_score: float
    confirmation_count: int = 0
    similarity: float = 0.0


class ValidationInfo(BaseModel):
    performed: bool = False
    agreed: bool | None = None
    overridden: bool = False


class IntelligentRouteResult(BaseModel):
    content: str
    source: ResponseSource
    provider: str
    model: str
    confidence: float
    task_type: TaskType
    similar_cases: list[KnowledgeCase] = Field(default_factory=list)
    latency_ms: int = 0
    tokens_used: int = 0
    used_online: bool = False
    kb_hits: int = 0
    low_accuracy_warning: bool = False
    strong_match: bool = False
    kb_mode: Literal["semantic", "hash", "disabled"] = "disabled"
    validation: ValidationInfo = Field(default_factory=ValidationInfo)
    metadata: dict[str, Any] = Field(default_factory=dict)
