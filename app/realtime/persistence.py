"""Restore realtime sessions from persisted snapshots."""

from __future__ import annotations

from app.realtime.payloads import ChatMessagePayload, DiagnosticTestPayload, SessionSnapshotPayload
from app.realtime.session_state import RealtimeSessionData, utc_now


def snapshot_dict_to_session(payload: dict) -> RealtimeSessionData:
    snap = SessionSnapshotPayload.model_validate(payload)
    ctx = snap.session
    messages = [
        ChatMessagePayload.model_validate(m) if not isinstance(m, ChatMessagePayload) else m
        for m in snap.conversation
    ]
    diagnostics = [
        DiagnosticTestPayload.model_validate(d) if not isinstance(d, DiagnosticTestPayload) else d
        for d in snap.diagnostic_state
    ]
    return RealtimeSessionData(
        session_id=ctx.id,
        label=ctx.label,
        device=ctx.device,
        issue=ctx.issue,
        status=ctx.status,
        diagnosis_label=ctx.diagnosis_label,
        messages=list(messages),
        diagnostics=list(diagnostics),
        assistant_status=snap.assistant_status,
        state_version=snap.state_version,
        pc_agent=None,
        created_at=utc_now(),
    )


def persistable_snapshot(session: RealtimeSessionData) -> dict:
    data = session.snapshot().model_dump(mode="json")
    data["participants"] = []
    data["pc_agent"] = None
    return data
