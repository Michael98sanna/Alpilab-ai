import { describe, it, expect } from "vitest";
import { applySessionChanges } from "../realtime/applyStateChanges";
import { mapRealtimeEventToActions, mapWsMessageToActions, shouldRequestSnapshot } from "../realtime/mapEvents";
import type { RepairState } from "../types";
import type { SessionSnapshot } from "../realtime/types";

function reduceState(state: RepairState, action: ReturnType<typeof mapRealtimeEventToActions>[number]): RepairState {
  if (action.type === "APPLY_STATE_UPDATE") {
    if (action.stateVersion <= state.stateVersion) return state;
    const updated = applySessionChanges(state, action.changes);
    return { ...updated, stateVersion: action.stateVersion };
  }
  if (action.type === "STATE_UPDATE_REJECTED") {
    return {
      ...state,
      stateVersion: Math.max(state.stateVersion, action.stateVersion),
      savingTestId: null,
      stateError: action.reason,
    };
  }
  return state;
}

const baseState: RepairState = {
  session: {
    id: "repair-1",
    label: "Repair #001",
    device: "iPhone 13 Pro",
    issue: "No Power",
    status: "active",
    diagnosisLabel: "Diagnosis in progress",
  },
  messages: [],
  tests: [
    { id: "t3", name: "PP_VDD_MAIN", status: "PENDING" },
  ],
  tools: [],
  devices: [],
  coreState: "IDLE",
  onboardingStep: "complete",
  toolsExpanded: false,
  activeToolPanel: null,
  diagnosticsExpanded: false,
  contextPanelExpanded: false,
  sessionDevicesExpanded: false,
  connectionState: "CONNECTED",
  pendingMessageIds: [],
  stateVersion: 1,
  savingTestId: "t3",
  stateError: null,
  pcAgent: null,
};

describe("mapEvents state sync", () => {
  it("maps SESSION_STATE_UPDATED to APPLY_STATE_UPDATE", () => {
    const actions = mapRealtimeEventToActions({
      id: "e1",
      repair_session_id: "repair-1",
      event_type: "SESSION_STATE_UPDATED",
      payload: {
        state_version: 2,
        changes: {
          diagnostic_test: {
            id: "t3",
            name: "PP_VDD_MAIN",
            value: "0.500 V",
            status: "PASSED",
          },
        },
      },
    });
    expect(actions[0]).toEqual({
      type: "APPLY_STATE_UPDATE",
      stateVersion: 2,
      changes: {
        diagnostic_test: {
          id: "t3",
          name: "PP_VDD_MAIN",
          value: "0.500 V",
          status: "PASSED",
        },
      },
    });
  });

  it("maps STATE_UPDATE_REJECTED", () => {
    const actions = mapRealtimeEventToActions({
      id: "e2",
      repair_session_id: "repair-1",
      event_type: "STATE_UPDATE_REJECTED",
      payload: { reason: "invalid measurement", state_version: 2 },
    });
    expect(actions[0]?.type).toBe("STATE_UPDATE_REJECTED");
  });

  it("detects snapshot gap", () => {
    expect(shouldRequestSnapshot(10, 12)).toBe(true);
    expect(shouldRequestSnapshot(10, 11)).toBe(false);
    expect(shouldRequestSnapshot(12, 12)).toBe(false);
  });
});

describe("applySessionChanges", () => {
  it("applies diagnostic measurement update", () => {
    const next = applySessionChanges(baseState, {
      diagnostic_test: {
        id: "t3",
        name: "PP_VDD_MAIN",
        value: "0.500 V",
        status: "PASSED",
      },
    });
    expect(next.tests[0]?.value).toBe("0.500 V");
    expect(next.tests[0]?.status).toBe("PASSED");
    expect(next.savingTestId).toBeNull();
  });

  it("applies pause/resume repair context", () => {
    const paused = applySessionChanges(baseState, {
      repair_context: {
        status: "paused",
        diagnosis_label: "Diagnosis paused",
      },
    });
    expect(paused.session.status).toBe("paused");
    expect(paused.session.diagnosisLabel).toBe("Diagnosis paused");

    const resumed = applySessionChanges(paused, {
      repair_context: {
        status: "active",
        diagnosis_label: "Diagnosis in progress",
      },
    });
    expect(resumed.session.status).toBe("active");
  });

  it("applies assistant status", () => {
    const next = applySessionChanges(baseState, { assistant_status: "THINKING" });
    expect(next.coreState).toBe("THINKING");
  });

  it("ignores duplicate state version", () => {
    const action = mapRealtimeEventToActions({
      id: "e-dup",
      repair_session_id: "repair-1",
      event_type: "SESSION_STATE_UPDATED",
      payload: {
        state_version: 1,
        changes: {
          diagnostic_test: { id: "t3", name: "PP_VDD_MAIN", value: "0.100 V", status: "PASSED" },
        },
      },
    })[0];
    const next = reduceState(baseState, action!);
    expect(next.stateVersion).toBe(1);
    expect(next.tests[0]?.value).toBeUndefined();
  });

  it("handles rejected update", () => {
    const action = mapRealtimeEventToActions({
      id: "e-rej",
      repair_session_id: "repair-1",
      event_type: "STATE_UPDATE_REJECTED",
      payload: { reason: "diagnosis is paused", state_version: 2 },
    })[0];
    const next = reduceState(baseState, action!);
    expect(next.stateError).toBe("diagnosis is paused");
    expect(next.savingTestId).toBeNull();
  });

  it("maps AGENT_CONNECTED to SET_PC_AGENT", () => {
    const actions = mapRealtimeEventToActions({
      id: "e-agent",
      repair_session_id: "repair-1",
      event_type: "AGENT_CONNECTED",
      payload: {
        agent_id: "agent-abc",
        agent_name: "ALPILAB-PC",
        platform: "windows",
        agent_version: "0.1.0",
        online: true,
      },
    });
    expect(actions[0]).toEqual({
      type: "SET_PC_AGENT",
      agent: {
        agentId: "agent-abc",
        agentName: "ALPILAB-PC",
        online: true,
        status: "ONLINE",
        platform: "windows",
        agentVersion: "0.1.0",
      },
    });
  });
});

describe("snapshot hydration", () => {
  it("includes state_version in APPLY_SNAPSHOT mapping", () => {
    const snapshot: SessionSnapshot = {
      session: {
        id: "repair-1",
        label: "Repair #001",
        device: "iPhone",
        issue: "No Power",
        status: "active",
        diagnosis_label: "In progress",
      },
      participants: [],
      conversation: [],
      repair_context: {
        id: "repair-1",
        label: "Repair #001",
        device: "iPhone",
        issue: "No Power",
        status: "active",
        diagnosis_label: "In progress",
      },
      diagnostic_state: [
        { id: "t3", name: "PP_VDD_MAIN", value: "0.500 V", status: "PASSED" },
      ],
      assistant_status: "IDLE",
      state_version: 5,
    };
    const actions = mapWsMessageToActions({ type: "snapshot", payload: snapshot });
    expect(actions[0]?.type).toBe("APPLY_SNAPSHOT");
    if (actions[0]?.type === "APPLY_SNAPSHOT") {
      expect(actions[0].snapshot.state_version).toBe(5);
    }
  });
});
