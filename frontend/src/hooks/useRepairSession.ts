import { useCallback, useReducer } from "react";
import type { DiagnosticStatus, RepairState, ToolId } from "../types";
import { mapDiagnosticStatus } from "../realtime/types";
import { applySessionChanges } from "../realtime/applyStateChanges";
import {
  emptySession,
  initialDevices,
  initialMessages,
  initialSession,
  initialTests,
  initialTools,
  mockAiResponse,
  mockVoiceTranscript,
  MOCK_SESSION_LABEL,
  newRepairPrompts,
} from "../mock/scenario";

function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function nowTime(): string {
  return new Date().toLocaleTimeString("it-IT", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

const defaultUiState = {
  toolsExpanded: false,
  activeToolPanel: null as ToolId | null,
  diagnosticsExpanded: false,
  contextPanelExpanded: false,
  sessionDevicesExpanded: false,
  connectionState: "DISCONNECTED" as import("../types").ConnectionState,
  pendingMessageIds: [] as string[],
  stateVersion: 0,
  savingTestId: null as string | null,
  stateError: null as string | null,
  pcAgent: null as import("../types").PcAgentStatus | null,
};

function buildInitialState(): RepairState {
  return {
    session: { ...emptySession },
    messages: [],
    tests: [],
    tools: initialTools.map((t) => ({ ...t, open: false })),
    devices: initialDevices.map((d) => ({ ...d })),
    coreState: "IDLE",
    onboardingStep: "idle",
    ...defaultUiState,
  };
}

function buildScenarioState(): RepairState {
  return {
    session: { ...initialSession },
    messages: [...initialMessages],
    tests: [...initialTests],
    tools: initialTools.map((t) => ({ ...t })),
    devices: initialDevices.map((d) => ({ ...d })),
    coreState: "IDLE",
    onboardingStep: "complete",
    ...defaultUiState,
  };
}

type Action = import("../types").RepairAction;

function repairReducer(state: RepairState, action: Action): RepairState {
  switch (action.type) {
    case "LOAD_SCENARIO":
      return buildScenarioState();

    case "START_NEW_REPAIR":
      return {
        ...buildInitialState(),
        onboardingStep: "device",
        session: {
          id: createId(),
          label: MOCK_SESSION_LABEL,
          device: null,
          issue: null,
          status: "active",
          diagnosisLabel: "Setup",
        },
        messages: [
          {
            id: createId(),
            role: "assistant",
            content: newRepairPrompts.start,
            timestamp: nowTime(),
          },
        ],
        coreState: "IDLE",
      };

    case "SET_ONBOARDING_DEVICE":
      return {
        ...state,
        session: { ...state.session, device: action.device },
        onboardingStep: "issue",
        messages: [
          ...state.messages,
          {
            id: createId(),
            role: "user",
            content: action.device,
            timestamp: nowTime(),
          },
          {
            id: createId(),
            role: "assistant",
            content: newRepairPrompts.issue,
            timestamp: nowTime(),
          },
        ],
      };

    case "SET_ONBOARDING_ISSUE":
      return {
        ...state,
        session: {
          ...state.session,
          issue: action.issue,
          diagnosisLabel: "Diagnosis in progress",
        },
        onboardingStep: "complete",
        coreState: "WORKING",
        tests: [
          { id: createId(), name: "Battery voltage", status: "PENDING" },
          { id: createId(), name: "USB communication", status: "PENDING" },
          { id: createId(), name: "PP_VDD_MAIN", status: "PENDING" },
        ],
        messages: [
          ...state.messages,
          {
            id: createId(),
            role: "user",
            content: action.issue,
            timestamp: nowTime(),
          },
          {
            id: createId(),
            role: "assistant",
            content: newRepairPrompts.complete,
            timestamp: nowTime(),
          },
        ],
      };

    case "ADD_MESSAGE":
      return { ...state, messages: [...state.messages, action.message] };

    case "SET_CORE_STATE":
      return { ...state, coreState: action.state };

    case "SET_DIAGNOSIS_PAUSED":
      return {
        ...state,
        session: {
          ...state.session,
          status: action.paused ? "paused" : "active",
          diagnosisLabel: action.paused
            ? "Diagnosis paused"
            : "Diagnosis in progress",
        },
      };

    case "UPDATE_TEST":
      return {
        ...state,
        tests: state.tests.map((t) =>
          t.id === action.testId
            ? { ...t, value: action.value, status: action.status }
            : t,
        ),
      };

    case "TOGGLE_TOOLS":
      return {
        ...state,
        toolsExpanded: !state.toolsExpanded,
        diagnosticsExpanded: false,
      };

    case "TOGGLE_DIAGNOSTICS":
      return {
        ...state,
        diagnosticsExpanded: !state.diagnosticsExpanded,
        toolsExpanded: false,
      };

    case "TOGGLE_CONTEXT_PANEL":
      return { ...state, contextPanelExpanded: !state.contextPanelExpanded };

    case "TOGGLE_SESSION_DEVICES":
      return {
        ...state,
        sessionDevicesExpanded: !state.sessionDevicesExpanded,
      };

    case "OPEN_TOOL":
      return {
        ...state,
        activeToolPanel: action.toolId,
        coreState: "WORKING",
        tools: state.tools.map((t) =>
          t.id === action.toolId ? { ...t, open: true } : t,
        ),
      };

    case "CLOSE_TOOL_PANEL":
      return {
        ...state,
        activeToolPanel: null,
        tools: state.tools.map((t) => ({ ...t, open: false })),
        coreState: state.coreState === "WORKING" ? "IDLE" : state.coreState,
      };

    case "SET_CONNECTION_STATE":
      return { ...state, connectionState: action.state };

    case "ADD_PENDING_MESSAGE":
      return {
        ...state,
        pendingMessageIds: [...state.pendingMessageIds, action.clientId],
      };

    case "REMOVE_PENDING_MESSAGE":
      return {
        ...state,
        pendingMessageIds: state.pendingMessageIds.filter((id) => id !== action.clientId),
      };

    case "APPLY_SNAPSHOT": {
      const snap = action.snapshot;
      return {
        ...state,
        session: {
          id: snap.session.id,
          label: snap.session.label,
          device: snap.session.device,
          issue: snap.session.issue,
          status: snap.session.status === "paused" ? "paused" : "active",
          diagnosisLabel: snap.session.diagnosis_label,
        },
        messages: snap.conversation.map((m) => ({
          id: m.message_id,
          role: m.role,
          content: m.content,
          timestamp: m.timestamp,
        })),
        tests: snap.diagnostic_state.map((t) => ({
          id: t.id,
          name: t.name,
          value: t.value,
          status: mapDiagnosticStatus(t.status),
        })),
        devices: snap.participants.map((p) => ({
          id: p.device_id,
          kind: p.device_type,
          label: p.device_name,
          online: p.online,
        })),
        coreState: snap.assistant_status,
        onboardingStep: snap.session.device && snap.session.issue ? "complete" : "idle",
        stateVersion: snap.state_version ?? 0,
        savingTestId: null,
        stateError: null,
        pcAgent: snap.pc_agent
          ? {
              agentId: snap.pc_agent.agent_id,
              agentName: snap.pc_agent.agent_name,
              online: snap.pc_agent.online,
              status: snap.pc_agent.status,
              platform: snap.pc_agent.platform,
              agentVersion: snap.pc_agent.agent_version,
            }
          : null,
      };
    }

    case "SET_PC_AGENT":
      return { ...state, pcAgent: action.agent };

    case "APPLY_STATE_UPDATE": {
      if (action.stateVersion <= state.stateVersion) {
        return state;
      }
      const updated = applySessionChanges(state, action.changes);
      const onboardingStep =
        updated.session.device && updated.session.issue
          ? "complete"
          : updated.onboardingStep;
      return {
        ...updated,
        onboardingStep,
        stateVersion: action.stateVersion,
      };
    }

    case "SET_SAVING_TEST":
      return { ...state, savingTestId: action.testId, stateError: null };

    case "SET_STATE_ERROR":
      return { ...state, stateError: action.message, savingTestId: null };

    case "STATE_UPDATE_REJECTED":
      return {
        ...state,
        stateVersion: Math.max(state.stateVersion, action.stateVersion),
        savingTestId: null,
        stateError: action.reason,
      };

    case "APPLY_DEVICE_PRESENCE": {
      const existing = state.devices.find((d) => d.id === action.deviceId);
      if (existing) {
        return {
          ...state,
          devices: state.devices.map((d) =>
            d.id === action.deviceId
              ? { ...d, online: action.online, label: action.label }
              : d,
          ),
        };
      }
      return {
        ...state,
        devices: [
          ...state.devices,
          {
            id: action.deviceId,
            kind: action.deviceType,
            label: action.label,
            online: action.online,
          },
        ],
      };
    }

    case "SYNC_DIAGNOSTICS":
      return { ...state, tests: action.tests };

    default:
      return state;
  }
}

export function useRepairSession(loadScenarioOnInit = true) {
  const [state, dispatch] = useReducer(
    repairReducer,
    loadScenarioOnInit ? buildScenarioState() : buildInitialState(),
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      dispatch({
        type: "ADD_MESSAGE",
        message: {
          id: createId(),
          role: "user",
          content: trimmed,
          timestamp: nowTime(),
        },
      });

      if (state.onboardingStep === "device") {
        dispatch({ type: "SET_ONBOARDING_DEVICE", device: trimmed });
        return;
      }

      if (state.onboardingStep === "issue") {
        dispatch({ type: "SET_ONBOARDING_ISSUE", issue: trimmed });
        return;
      }

      dispatch({ type: "SET_CORE_STATE", state: "THINKING" });
      await new Promise((r) => setTimeout(r, 600));

      const lower = trimmed.toLowerCase();
      if (lower.includes("fermati") || lower.includes("pausa")) {
        dispatch({ type: "SET_DIAGNOSIS_PAUSED", paused: true });
      }
      if (lower.includes("continua")) {
        dispatch({ type: "SET_DIAGNOSIS_PAUSED", paused: false });
      }

      const response = mockAiResponse(trimmed);
      dispatch({ type: "SET_CORE_STATE", state: "SPEAKING" });
      await new Promise((r) => setTimeout(r, 400));

      dispatch({
        type: "ADD_MESSAGE",
        message: {
          id: createId(),
          role: "assistant",
          content: response,
          timestamp: nowTime(),
        },
      });
      dispatch({ type: "SET_CORE_STATE", state: "IDLE" });
    },
    [state.onboardingStep],
  );

  const simulateVoice = useCallback(async () => {
    dispatch({ type: "SET_CORE_STATE", state: "LISTENING" });
    await new Promise((r) => setTimeout(r, 900));

    const transcript = mockVoiceTranscript();
    dispatch({
      type: "ADD_MESSAGE",
      message: {
        id: createId(),
        role: "user",
        content: transcript,
        timestamp: nowTime(),
      },
    });

    dispatch({ type: "SET_CORE_STATE", state: "THINKING" });
    await new Promise((r) => setTimeout(r, 500));
    dispatch({ type: "SET_CORE_STATE", state: "SPEAKING" });
    await new Promise((r) => setTimeout(r, 400));

    dispatch({
      type: "ADD_MESSAGE",
      message: {
        id: createId(),
        role: "assistant",
        content: mockAiResponse(transcript),
        timestamp: nowTime(),
      },
    });
    dispatch({ type: "SET_CORE_STATE", state: "IDLE" });
  }, []);

  const submitMeasurement = useCallback(
    (testId: string, value: string) => {
      const num = parseFloat(value);
      const status: DiagnosticStatus =
        num === 0 ? "FAILED" : num > 0 ? "PASSED" : "INVALID";
      const formatted = value.includes("V") ? value : `${value} V`;
      dispatch({
        type: "UPDATE_TEST",
        testId,
        value: formatted,
        status,
      });
      dispatch({ type: "SET_CORE_STATE", state: "WORKING" });
      setTimeout(() => {
        dispatch({ type: "SET_CORE_STATE", state: "IDLE" });
      }, 800);
      dispatch({
        type: "ADD_MESSAGE",
        message: {
          id: createId(),
          role: "system",
          content: `Misura registrata: ${formatted} — ${status}`,
          timestamp: nowTime(),
        },
      });
    },
    [],
  );

  const startNewRepair = useCallback(() => {
    dispatch({ type: "START_NEW_REPAIR" });
  }, []);

  const loadScenario = useCallback(() => {
    dispatch({ type: "LOAD_SCENARIO" });
  }, []);

  const pauseDiagnosis = useCallback(() => {
    dispatch({ type: "SET_DIAGNOSIS_PAUSED", paused: true });
    dispatch({
      type: "ADD_MESSAGE",
      message: {
        id: createId(),
        role: "system",
        content: "Diagnosi in pausa.",
        timestamp: nowTime(),
      },
    });
  }, []);

  const resumeDiagnosis = useCallback(() => {
    dispatch({ type: "SET_DIAGNOSIS_PAUSED", paused: false });
    dispatch({
      type: "ADD_MESSAGE",
      message: {
        id: createId(),
        role: "system",
        content: "Diagnosi ripresa.",
        timestamp: nowTime(),
      },
    });
  }, []);

  const toggleTools = useCallback(() => {
    dispatch({ type: "TOGGLE_TOOLS" });
  }, []);

  const toggleDiagnostics = useCallback(() => {
    dispatch({ type: "TOGGLE_DIAGNOSTICS" });
  }, []);

  const openDiagnostics = useCallback(() => {
    if (!state.diagnosticsExpanded) {
      dispatch({ type: "TOGGLE_DIAGNOSTICS" });
    }
  }, [state.diagnosticsExpanded]);

  const openTools = useCallback(() => {
    if (!state.toolsExpanded) {
      dispatch({ type: "TOGGLE_TOOLS" });
    }
  }, [state.toolsExpanded]);

  const closeDiagnostics = useCallback(() => {
    if (state.diagnosticsExpanded) {
      dispatch({ type: "TOGGLE_DIAGNOSTICS" });
    }
  }, [state.diagnosticsExpanded]);

  const closeTools = useCallback(() => {
    if (state.toolsExpanded) {
      dispatch({ type: "TOGGLE_TOOLS" });
    }
  }, [state.toolsExpanded]);

  const toggleContextPanel = useCallback(() => {
    dispatch({ type: "TOGGLE_CONTEXT_PANEL" });
  }, []);

  const toggleSessionDevices = useCallback(() => {
    dispatch({ type: "TOGGLE_SESSION_DEVICES" });
  }, []);

  const openTool = useCallback((toolId: ToolId) => {
    dispatch({ type: "OPEN_TOOL", toolId });
  }, []);

  const closeToolPanel = useCallback(() => {
    dispatch({ type: "CLOSE_TOOL_PANEL" });
  }, []);

  const nextPendingTest = state.tests.find((t) => t.status === "PENDING");

  return {
    state,
    dispatch,
    sendMessage,
    simulateVoice,
    submitMeasurement,
    startNewRepair,
    loadScenario,
    pauseDiagnosis,
    resumeDiagnosis,
    toggleTools,
    toggleDiagnostics,
    openDiagnostics,
    openTools,
    closeDiagnostics,
    closeTools,
    toggleContextPanel,
    toggleSessionDevices,
    openTool,
    closeToolPanel,
    nextPendingTest,
    hasActiveRepair: state.session.status !== "none",
  };
}

export type RepairSessionApi = ReturnType<typeof useRepairSession>;
