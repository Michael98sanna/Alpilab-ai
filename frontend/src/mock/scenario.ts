import type {
  ChatMessage,
  DiagnosticTest,
  RepairSession,
  SessionDevice,
  ToolItem,
} from "../types";

export const MOCK_SESSION_LABEL = "Repair #001";

export const initialSession: RepairSession = {
  id: "repair-001",
  label: MOCK_SESSION_LABEL,
  device: "iPhone 13 Pro",
  issue: "No Power",
  status: "active",
  diagnosisLabel: "Diagnosis in progress",
};

export const initialMessages: ChatMessage[] = [
  {
    id: "m1",
    role: "assistant",
    content: "Sessione attiva. iPhone 13 Pro — problema: non si accende.",
    timestamp: "09:12",
  },
  {
    id: "m2",
    role: "assistant",
    content: "Ho registrato Battery voltage: 3.81 V — PASSED.",
    timestamp: "09:14",
  },
  {
    id: "m3",
    role: "user",
    content: "USB communication risulta KO.",
    timestamp: "09:15",
  },
  {
    id: "m4",
    role: "assistant",
    content:
      "Confermato. USB communication FAILED. Il prossimo passo consigliato è misurare PP_VDD_MAIN.",
    timestamp: "09:15",
  },
  {
    id: "m5",
    role: "assistant",
    content: "Inserisci la misura quando sei pronto, oppure chiedi se serve assistenza.",
    timestamp: "09:16",
  },
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
