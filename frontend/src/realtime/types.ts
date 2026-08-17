import type { CoreState, DeviceKind, DiagnosticStatus, MessageRole } from "../types";

export type RealtimeEventType =
  | "SESSION_SNAPSHOT"
  | "CHAT_MESSAGE"
  | "ASSISTANT_STATUS"
  | "DEVICE_CONNECTED"
  | "DEVICE_DISCONNECTED"
  | "DEVICE_HEARTBEAT"
  | "DIAGNOSTIC_UPDATED"
  | "DIAGNOSTIC_TEST_STARTED"
  | "DIAGNOSTIC_TEST_COMPLETED";

export interface RealtimeEventEnvelope {
  id: string;
  repair_session_id: string;
  event_type: RealtimeEventType | string;
  payload: Record<string, unknown>;
  source_client_device_id?: string | null;
}

export interface WsServerMessage {
  type: "event" | "snapshot" | "error" | "ack";
  event?: RealtimeEventEnvelope;
  payload?: SessionSnapshot;
  message?: string;
}

export interface SessionSnapshot {
  session: {
    id: string;
    label: string;
    device: string | null;
    issue: string | null;
    status: string;
    diagnosis_label: string;
  };
  participants: Array<{
    device_id: string;
    device_type: DeviceKind;
    device_name: string;
    online: boolean;
  }>;
  conversation: Array<{
    message_id: string;
    role: MessageRole;
    content: string;
    timestamp: string;
  }>;
  repair_context: SessionSnapshot["session"];
  diagnostic_state: Array<{
    id: string;
    name: string;
    value?: string;
    status: string;
  }>;
  assistant_status: CoreState;
}

export interface RealtimeClientOptions {
  sessionId: string;
  deviceId: string;
  deviceType: DeviceKind;
  deviceName: string;
  seedDemo?: boolean;
  onMessage: (msg: WsServerMessage) => void;
  onConnectionChange: (state: import("../config/env").ConnectionState) => void;
}

export type OutboundMessage =
  | { type: "chat_message"; content: string; role: MessageRole }
  | { type: "heartbeat" }
  | { type: "assistant_status"; status: CoreState };

export function mapDiagnosticStatus(status: string): DiagnosticStatus {
  const upper = status.toUpperCase();
  if (upper === "PASSED") return "PASSED";
  if (upper === "FAILED") return "FAILED";
  if (upper === "IN_PROGRESS") return "IN_PROGRESS";
  if (upper === "SKIPPED") return "SKIPPED";
  if (upper === "INVALID") return "INVALID";
  return "PENDING";
}
