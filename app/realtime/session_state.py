"""In-memory repair session state for realtime V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.realtime.payloads import (
    AssistantStatus,
    ChatMessagePayload,
    DevicePresencePayload,
    DeviceType,
    DiagnosticTestPayload,
    RepairContextPayload,
    SessionSnapshotPayload,
)

from app.agent.payloads import AgentPresencePayload
from app.conversation.alpilab_check_context import ProductSearchContext
from app.schemas.device_context import DetectedDevice, DeviceContext


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ConnectedDevice:
    device_id: str
    device_type: DeviceType
    device_name: str
    connected_at: datetime
    last_seen: datetime
    online: bool = True


@dataclass
class RealtimeSessionData:
    session_id: str
    label: str = "Repair Session"
    device: str | None = None
    issue: str | None = None
    status: str = "active"
    diagnosis_label: str = "Diagnosis in progress"
    messages: list[ChatMessagePayload] = field(default_factory=list)
    devices: dict[str, ConnectedDevice] = field(default_factory=dict)
    diagnostics: list[DiagnosticTestPayload] = field(default_factory=list)
    assistant_status: AssistantStatus = "IDLE"
    state_version: int = 0
    pc_agent: AgentPresencePayload | None = None
    device_context: DeviceContext | None = None
    detected_devices: list[DetectedDevice] = field(default_factory=list)
    product_search_context: ProductSearchContext | None = None
    created_at: datetime = field(default_factory=utc_now)

    def repair_context(self) -> RepairContextPayload:
        return RepairContextPayload(
            id=self.session_id,
            label=self.label,
            device=self.device,
            issue=self.issue,
            status=self.status,
            diagnosis_label=self.diagnosis_label,
        )

    def participants(self) -> list[DevicePresencePayload]:
        return [
            DevicePresencePayload(
                device_id=d.device_id,
                device_type=d.device_type,
                device_name=d.device_name,
                online=d.online,
                connected_at=d.connected_at,
                last_seen=d.last_seen,
            )
            for d in self.devices.values()
        ]

    def snapshot(self) -> SessionSnapshotPayload:
        ctx = self.repair_context()
        return SessionSnapshotPayload(
            session=ctx,
            participants=self.participants(),
            conversation=list(self.messages),
            repair_context=ctx,
            diagnostic_state=list(self.diagnostics),
            assistant_status=self.assistant_status,
            state_version=self.state_version,
            pc_agent=self.pc_agent,
            device_context=self.device_context.model_dump(mode="json") if self.device_context else None,
            detected_devices=[d.model_dump(mode="json") for d in self.detected_devices],
        )


def default_demo_session(session_id: str) -> RealtimeSessionData:
    """Seed session resembling the approved UI mock scenario."""
    return RealtimeSessionData(
        session_id=session_id,
        label="Repair #001",
        device="iPhone 13 Pro",
        issue="No Power",
        status="active",
        diagnosis_label="Diagnosis in progress",
        messages=[
            ChatMessagePayload(
                message_id="m1",
                session_id=session_id,
                role="assistant",
                content="Dimmi cosa dobbiamo riparare.",
                timestamp="09:10",
            ),
            ChatMessagePayload(
                message_id="m2",
                session_id=session_id,
                device_id="phone-seed",
                role="user",
                content="iPhone 13 Pro che non si accende.",
                timestamp="09:11",
            ),
            ChatMessagePayload(
                message_id="m3",
                session_id=session_id,
                role="assistant",
                content="Ricevuto. Iniziamo la diagnosi.",
                timestamp="09:11",
            ),
        ],
        diagnostics=[
            DiagnosticTestPayload(
                id="t1",
                name="Battery voltage",
                value="3.81 V",
                status="PASSED",
            ),
            DiagnosticTestPayload(
                id="t2",
                name="USB communication",
                value="FAILED",
                status="FAILED",
            ),
            DiagnosticTestPayload(id="t3", name="PP_VDD_MAIN", status="PENDING"),
        ],
    )


def default_repair_diagnostics() -> list[DiagnosticTestPayload]:
    """Standard measurement workflow shown in the Diagnosi panel."""
    return [
        DiagnosticTestPayload(id="t1", name="Battery voltage", status="PENDING"),
        DiagnosticTestPayload(id="t2", name="USB communication", status="PENDING"),
        DiagnosticTestPayload(id="t3", name="PP_VDD_MAIN", status="PENDING"),
    ]


def new_session(session_id: str | None = None) -> RealtimeSessionData:
    sid = session_id or str(uuid4())
    return RealtimeSessionData(session_id=sid, label=f"Repair {sid[:8]}")


def session_is_unseeded(session: RealtimeSessionData) -> bool:
    """True when the session has no repair context or demo content yet."""
    return (
        session.device is None
        and session.issue is None
        and not session.messages
        and not session.diagnostics
    )


def apply_demo_seed(session: RealtimeSessionData) -> None:
    """Fill an empty session with the approved demo scenario (preserves devices/agent)."""
    demo = default_demo_session(session.session_id)
    session.label = demo.label
    session.device = demo.device
    session.issue = demo.issue
    session.status = demo.status
    session.diagnosis_label = demo.diagnosis_label
    session.messages = list(demo.messages)
    session.diagnostics = list(demo.diagnostics)
    session.state_version += 1
