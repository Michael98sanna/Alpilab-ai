"""Restore realtime sessions from persisted snapshots."""

from __future__ import annotations

from app.realtime.payloads import ChatMessagePayload, DiagnosticTestPayload, SessionSnapshotPayload
from app.realtime.session_state import RealtimeSessionData, utc_now
from app.schemas.device_context import DeviceContext


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
    device_context = DeviceContext.model_validate(snap.device_context) if snap.device_context else None
    # USB scan results are ephemeral — never restore a stale detected list after restart.
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
        device_context=device_context,
        detected_devices=[],
        created_at=utc_now(),
    )


def persistable_snapshot(session: RealtimeSessionData) -> dict:
    data = session.snapshot().model_dump(mode="json")
    data["participants"] = []
    data["pc_agent"] = None
    # Do not persist live ADB/USB scan results across app restarts.
    data["detected_devices"] = []
    return data
