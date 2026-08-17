export type CoreState =
  | "IDLE"
  | "LISTENING"
  | "THINKING"
  | "SPEAKING"
  | "WORKING"
  | "WARNING"
  | "ERROR";

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
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
  | { type: "LOAD_SCENARIO" };
