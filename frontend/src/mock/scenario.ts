import type {
  ChatMessage,
  CoreState,
  DiagnosticTest,
  RepairSession,
  SessionDevice,
  ToolItem,
} from "../types";
import { STATUS_LABELS } from "../types";

export const MOCK_SESSION_LABEL = "Repair #001";

export const initialSession: RepairSession = {
  id: "repair-001",
  label: MOCK_SESSION_LABEL,
  device: "iPhone 13 Pro",
  issue: "No Power",
  status: "active",
  diagnosisLabel: "Diagnosis in progress",
};

function statusMsg(state: CoreState, id: string, time: string): ChatMessage {
  return {
    id,
    role: "status",
    content: STATUS_LABELS[state],
    timestamp: time,
    coreState: state,
  };
}

export const initialMessages: ChatMessage[] = [
  {
    id: "m1",
    role: "assistant",
    content: "Dimmi cosa dobbiamo riparare.",
    timestamp: "09:10",
  },
  {
    id: "m2",
    role: "user",
    content: "iPhone 13 Pro che non si accende.",
    timestamp: "09:11",
  },
  {
    id: "m3",
    role: "assistant",
    content: "Ricevuto. Iniziamo la diagnosi.",
    timestamp: "09:11",
  },
  statusMsg("WORKING", "s1", "09:12"),
  {
    id: "m4",
    role: "assistant",
    content: "Misura la tensione della batteria.",
    timestamp: "09:12",
  },
  {
    id: "m5",
    role: "user",
    content: "3.81 V",
    timestamp: "09:14",
  },
  {
    id: "m6",
    role: "assistant",
    content:
      "Valore corretto. La batteria non sembra essere il problema principale.",
    timestamp: "09:14",
  },
  statusMsg("THINKING", "s2", "09:15"),
  {
    id: "m7",
    role: "assistant",
    content: "Controlliamo ora la comunicazione USB.",
    timestamp: "09:15",
  },
  {
    id: "m8",
    role: "user",
    content: "USB communication risulta KO.",
    timestamp: "09:16",
  },
  {
    id: "m9",
    role: "assistant",
    content:
      "Confermato. USB FAILED. Il prossimo passo è misurare PP_VDD_MAIN.",
    timestamp: "09:16",
  },
  statusMsg("IDLE", "s3", "09:16"),
];

export const initialTests: DiagnosticTest[] = [
  { id: "t1", name: "Battery voltage", value: "3.81 V", status: "PASSED" },
  { id: "t2", name: "USB communication", value: "FAILED", status: "FAILED" },
  { id: "t3", name: "PP_VDD_MAIN", status: "PENDING" },
];

export const initialTools: ToolItem[] = [
  { id: "microscope", label: "Microscope", icon: "🔬", available: true, open: false },
  { id: "thermal", label: "Thermal", icon: "🌡️", available: true, open: false },
  { id: "multimeter", label: "Meter", icon: "📏", available: true, open: false },
  { id: "schematics", label: "Schematics", icon: "🗺️", available: true, open: false },
];

export const initialDevices: SessionDevice[] = [
  { id: "pc", kind: "pc", label: "PC", online: true },
  { id: "phone", kind: "phone", label: "Phone", online: true },
  { id: "tablet", kind: "tablet", label: "Tablet", online: false },
];

export const emptySession: RepairSession = {
  id: "",
  label: "",
  device: null,
  issue: null,
  status: "none",
  diagnosisLabel: "",
};

export const newRepairPrompts = {
  start: "Che dispositivo dobbiamo riparare?",
  issue: "Ricevuto. Qual è il problema?",
  complete: "Perfetto. Iniziamo la diagnosi.",
};

export function mockAiResponse(userText: string): string {
  const lower = userText.toLowerCase();
  if (lower.includes("fermati") || lower.includes("pausa")) {
    return "Diagnosi in pausa. I dati della sessione sono conservati.";
  }
  if (lower.includes("continua")) {
    return "Riprendo dal contesto esistente. PP_VDD_MAIN è ancora PENDING.";
  }
  if (lower.includes("pp_vdd") || lower.includes("misura")) {
    return "Inserisci il valore nel pannello diagnostico oppure scrivilo qui.";
  }
  return `[MOCK AI] Ho analizzato: "${userText}". Suggerisco verificare PP_VDD_MAIN.`;
}

export function mockVoiceTranscript(): string {
  return "Controlla la linea PP_VDD_MAIN sul multimetro.";
}

export function createStatusMessage(state: CoreState, id: string): ChatMessage {
  return {
    id,
    role: "status",
    content: STATUS_LABELS[state],
    timestamp: new Date().toLocaleTimeString("it-IT", {
      hour: "2-digit",
      minute: "2-digit",
    }),
    coreState: state,
  };
}
