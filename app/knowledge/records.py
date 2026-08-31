"""Input record for indexing repairs into the knowledge base."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.session import RepairSessionContext


class RepairKnowledgeRecord(BaseModel):
    """Normalized repair case stored in the knowledge base."""

    session_id: str
    device_model: str
    device_brand: str = ""
    symptoms: list[str] = Field(default_factory=list)
    diagnosis: str = ""
    solution: str = ""
    technical_notes: str = ""
    repair_duration_min: int | None = None
    status: str = "completed"

    @classmethod
    def from_session_context(cls, session: RepairSessionContext) -> RepairKnowledgeRecord:
        """Build a record from session metadata."""
        metadata = session.metadata or {}
        symptoms = metadata.get("symptoms", [])
        if isinstance(symptoms, str):
            symptoms = [symptoms]

        duration = metadata.get("duration_min")
        return cls(
            session_id=session.repair_session_id,
            device_model=str(metadata.get("device_model", "unknown")),
            device_brand=str(metadata.get("device_brand", "")),
            symptoms=[str(item) for item in symptoms],
            diagnosis=str(metadata.get("diagnosis", "")),
            solution=str(metadata.get("solution", "")),
            technical_notes=str(metadata.get("notes", "")),
            repair_duration_min=int(duration) if duration is not None else None,
            status=str(metadata.get("status", "completed")),
        )
