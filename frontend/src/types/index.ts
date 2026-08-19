export type CoreState =
  | "IDLE"
  | "LISTENING"
  | "THINKING"
  | "SPEAKING"
  | "WORKING"
  | "WARNING"
  | "ERROR";

export type MessageRole = "user" | "assistant" | "system" | "status";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  /** Present when role is "status" — assistant state in timeline */
  coreState?: CoreState;
}

export type DiagnosticStatus =
  | "PENDING"
  | "IN_PROGRESS"
  | "PASSED"
  | "FAILED"
  | "SKIPPED"
  | "INVALID";

export interface DiagnosticTest {
  id: string;
  name: string;
  value?: string;
  status: DiagnosticStatus;
}

export type ToolId = "microscope" | "thermal" | "multimeter" | "schematics";

export interface ToolItem {
  id: ToolId;
  label: string;
  icon: string;
  available: boolean;
  open: boolean;
}

export type DeviceKind = "pc" | "phone" | "tablet";

export interface SessionDevice {
  id: string;
  kind: DeviceKind;
  label: string;
  online: boolean;
}

export interface DetectedDevice {
  id: string;
  brand: string | null;
  model: string | null;
  variant: string | null;
  serial_number: string | null;
  connection_type: string;
  source: string;
  detected_at: string;
  metadata?: Record<string, unknown>;
}

export interface DeviceContext {
  id: string;
  brand: string | null;
  model: string | null;
  serial_number: string | null;
  connection_type: string | null;
  source: string | null;
  associated_at: string;
  color?: string | null;
  storage?: string | null;
  battery_health?: string | null;
}

export interface PcAgentStatus {
  agentId: string;
  agentName: string;
  online: boolean;
  status: string;
  platform: string;
  agentVersion: string;
}

export type RepairStatus = "none" | "active" | "paused";

export interface RepairSession {
  id: string;
  label: string;
  device: string | null;
  issue: string | null;
  status: RepairStatus;
  diagnosisLabel: string;
}

export type OnboardingStep = "idle" | "device" | "issue" | "complete";

export type ConnectionState =
  | "CONNECTING"
  | "CONNECTED"
  | "DISCONNECTED"
  | "RECONNECTING"
  | "ERROR";

export interface RepairState {
  session: RepairSession;
  messages: ChatMessage[];
  tests: DiagnosticTest[];
  tools: ToolItem[];
  devices: SessionDevice[];
  coreState: CoreState;
  onboardingStep: OnboardingStep;
  toolsExpanded: boolean;
  activeToolPanel: ToolId | null;
  diagnosticsExpanded: boolean;
  contextPanelExpanded: boolean;
  sessionDevicesExpanded: boolean;
  connectionState: ConnectionState;
  pendingMessageIds: string[];
  stateVersion: number;
  savingTestId: string | null;
  stateError: string | null;
  pcAgent: PcAgentStatus | null;
  detectedDevices: DetectedDevice[];
  deviceContext: DeviceContext | null;
}

export type RepairAction =
  | { type: "START_NEW_REPAIR" }
  | { type: "SET_ONBOARDING_DEVICE"; device: string }
  | { type: "SET_ONBOARDING_ISSUE"; issue: string }
  | { type: "ADD_MESSAGE"; message: ChatMessage }
  | { type: "SET_CORE_STATE"; state: CoreState }
  | { type: "SET_DIAGNOSIS_PAUSED"; paused: boolean }
  | { type: "UPDATE_TEST"; testId: string; value: string; status: DiagnosticStatus }
  | { type: "TOGGLE_TOOLS" }
  | { type: "OPEN_TOOL"; toolId: ToolId }
  | { type: "CLOSE_TOOL_PANEL" }
  | { type: "TOGGLE_DIAGNOSTICS" }
  | { type: "TOGGLE_CONTEXT_PANEL" }
  | { type: "TOGGLE_SESSION_DEVICES" }
  | { type: "LOAD_SCENARIO" }
  | { type: "SET_CONNECTION_STATE"; state: ConnectionState }
  | { type: "ADD_PENDING_MESSAGE"; clientId: string }
  | { type: "REMOVE_PENDING_MESSAGE"; clientId: string }
  | { type: "APPLY_SNAPSHOT"; snapshot: import("../realtime/types").SessionSnapshot }
  | { type: "APPLY_DEVICE_PRESENCE"; deviceId: string; deviceType: DeviceKind; label: string; online: boolean }
  | { type: "SYNC_DIAGNOSTICS"; tests: DiagnosticTest[] }
  | {
      type: "APPLY_STATE_UPDATE";
      stateVersion: number;
      changes: Record<string, unknown>;
    }
  | { type: "SET_SAVING_TEST"; testId: string | null }
  | { type: "SET_STATE_ERROR"; message: string | null }
  | { type: "STATE_UPDATE_REJECTED"; reason: string; stateVersion: number }
  | { type: "SET_PC_AGENT"; agent: PcAgentStatus | null }
  | { type: "SET_DETECTED_DEVICES"; devices: DetectedDevice[] }
  | { type: "SET_DEVICE_CONTEXT"; context: DeviceContext | null };

/** @deprecated Use CORE_STATUS_CONFIG from config/coreStatus */
export const STATUS_LABELS: Record<CoreState, string> = {
  IDLE: "ALPILAB AI",
  LISTENING: "STO ASCOLTANDO...",
  THINKING: "STO PENSANDO...",
  SPEAKING: "STO PARLANDO...",
  WORKING: "STO LAVORANDO...",
  WARNING: "ATTENZIONE",
  ERROR: "SI È VERIFICATO UN ERRORE",
};
