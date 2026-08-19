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
    case "SESSION_STATE_UPDATED":
      return [
        {
          type: "APPLY_STATE_UPDATE",
          stateVersion: Number(payload.state_version),
          changes: (payload.changes as Record<string, unknown>) ?? {},
        },
      ];
    case "STATE_UPDATE_REJECTED":
      return [
        {
          type: "STATE_UPDATE_REJECTED",
          reason: String(payload.reason ?? "update rejected"),
          stateVersion: Number(payload.state_version ?? 0),
        },
      ];
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
    case "AGENT_CONNECTED":
    case "AGENT_HEARTBEAT":
      return [
        {
          type: "SET_PC_AGENT",
          agent: {
            agentId: String(payload.agent_id),
            agentName: String(payload.agent_name),
            online: true,
            status: String(payload.status ?? "ONLINE"),
            platform: String(payload.platform ?? "windows"),
            agentVersion: String(payload.agent_version ?? "0.1.0"),
          },
        },
      ];
    case "AGENT_DISCONNECTED":
      return [
        {
          type: "SET_PC_AGENT",
          agent: {
            agentId: String(payload.agent_id),
            agentName: String(payload.agent_name ?? "PC Agent"),
            online: false,
            status: "OFFLINE",
            platform: String(payload.platform ?? "windows"),
            agentVersion: String(payload.agent_version ?? "0.1.0"),
          },
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
    case "REPAIR_DEVICE_DETECTED":
    case "REPAIR_DEVICE_LIST_UPDATED":
      if (Array.isArray(payload.detected_devices)) {
        return [
          {
            type: "SET_DETECTED_DEVICES",
            devices: payload.detected_devices as import("../types").DetectedDevice[],
          },
        ];
      }
      return [];
    case "REPAIR_DEVICE_ASSOCIATED":
      return [
        {
          type: "SET_DEVICE_CONTEXT",
          context: payload as import("../types").DeviceContext,
        },
      ];
    case "REPAIR_DEVICE_UNASSOCIATED":
      return [{ type: "SET_DEVICE_CONTEXT", context: null }];
    case "REPAIR_DEVICE_DISCONNECTED":
      // device_context stays — only detected list changes (no separate action needed,
      // the hub will send REPAIR_DEVICE_LIST_UPDATED after)
      return [];
    case "TOOL_EXECUTION_STARTED":
      return [{ type: "SET_CORE_STATE", state: "WORKING" }];
    case "TOOL_EXECUTION_COMPLETED": {
      if (payload.success === true) {
        return [];
      }
      return [{ type: "SET_CORE_STATE", state: "ERROR" }];
    }
    default:
      return [];
  }
}

export function shouldRequestSnapshot(
  currentVersion: number,
  incomingVersion: number,
): boolean {
  return incomingVersion > currentVersion + 1;
}
