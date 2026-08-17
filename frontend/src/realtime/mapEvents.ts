import type { RepairAction } from "../types";
import type { RealtimeEventEnvelope, SessionSnapshot, WsServerMessage } from "./types";
import { mapDiagnosticStatus } from "./types";

export function mapSnapshotToAction(snapshot: SessionSnapshot): RepairAction {
  return { type: "APPLY_SNAPSHOT", snapshot };
}

export function mapWsMessageToActions(msg: WsServerMessage): RepairAction[] {
  if (msg.type === "snapshot" && msg.payload) {
    return [mapSnapshotToAction(msg.payload)];
  }
  if (msg.type !== "event" || !msg.event) {
    return [];
  }
  return mapRealtimeEventToActions(msg.event);
}

export function mapRealtimeEventToActions(event: RealtimeEventEnvelope): RepairAction[] {
  const payload = event.payload;
  switch (event.event_type) {
    case "CHAT_MESSAGE":
      return [
        {
          type: "ADD_MESSAGE",
          message: {
            id: String(payload.message_id),
            role: payload.role as "user" | "assistant" | "system",
            content: String(payload.content),
            timestamp: String(payload.timestamp),
          },
        },
      ];
    case "ASSISTANT_STATUS":
      return [{ type: "SET_CORE_STATE", state: payload.status as import("../types").CoreState }];
    case "DEVICE_CONNECTED":
      return [
        {
          type: "APPLY_DEVICE_PRESENCE",
          deviceId: String(payload.device_id),
          deviceType: payload.device_type as import("../types").DeviceKind,
          label: String(payload.device_name),
          online: true,
        },
      ];
    case "DEVICE_DISCONNECTED":
    case "DEVICE_HEARTBEAT":
      return [
        {
          type: "APPLY_DEVICE_PRESENCE",
          deviceId: String(payload.device_id),
          deviceType: (payload.device_type as import("../types").DeviceKind) || "pc",
          label: String(payload.device_name || payload.device_id),
          online: Boolean(payload.online),
        },
      ];
    case "DIAGNOSTIC_UPDATED":
    case "DIAGNOSTIC_TEST_COMPLETED":
    case "DIAGNOSTIC_TEST_STARTED":
      if (Array.isArray(payload.tests)) {
        return [
          {
            type: "SYNC_DIAGNOSTICS",
            tests: payload.tests.map((t: Record<string, unknown>) => ({
              id: String(t.id),
              name: String(t.name),
              value: t.value ? String(t.value) : undefined,
              status: mapDiagnosticStatus(String(t.status)),
            })),
          },
        ];
      }
      return [];
    default:
      return [];
  }
}
