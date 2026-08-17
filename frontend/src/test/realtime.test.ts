import { describe, it, expect } from "vitest";
import { mapRealtimeEventToActions, mapWsMessageToActions } from "../realtime/mapEvents";
import type { SessionSnapshot } from "../realtime/types";

describe("mapEvents", () => {
  it("maps chat message event", () => {
    const actions = mapRealtimeEventToActions({
      id: "e1",
      repair_session_id: "s1",
      event_type: "CHAT_MESSAGE",
      payload: {
        message_id: "m1",
        content: "Ciao",
        role: "user",
        timestamp: "10:00",
      },
    });
    expect(actions[0]).toEqual({
      type: "ADD_MESSAGE",
      message: { id: "m1", role: "user", content: "Ciao", timestamp: "10:00" },
    });
  });

  it("maps assistant status event", () => {
    const actions = mapRealtimeEventToActions({
      id: "e2",
      repair_session_id: "s1",
      event_type: "ASSISTANT_STATUS",
      payload: { status: "THINKING" },
    });
    expect(actions[0]).toEqual({ type: "SET_CORE_STATE", state: "THINKING" });
  });

  it("maps session snapshot", () => {
    const snapshot: SessionSnapshot = {
      session: {
        id: "repair-1",
        label: "Repair #001",
        device: "iPhone",
        issue: "No Power",
        status: "active",
        diagnosis_label: "In progress",
      },
      participants: [
        { device_id: "pc-1", device_type: "pc", device_name: "PC", online: true },
      ],
      conversation: [],
      repair_context: {
        id: "repair-1",
        label: "Repair #001",
        device: "iPhone",
        issue: "No Power",
        status: "active",
        diagnosis_label: "In progress",
      },
      diagnostic_state: [],
      assistant_status: "IDLE",
    };
    const actions = mapWsMessageToActions({ type: "snapshot", payload: snapshot });
    expect(actions[0]?.type).toBe("APPLY_SNAPSHOT");
  });
});
