import { getApiBaseUrl } from "../config/env";

export interface DiagnosticCard {
  id: string;
  session_id?: string;
  device_name: string;
  device_id: string;
  status: string;
  current_symptom?: string;
  hypothesis?: string;
  confidence: number;
  created_at: string;
  updated_at: string;
  diagnostic_stage: string;
}

export interface DiagnosticMessage {
  role: string;
  content: string;
  timestamp: string;
}

export interface DiagnosticCardSummary {
  device: string;
  status: string;
  started: string;
  updated: string;
  current_symptom?: string;
  hypothesis?: string;
  confidence: number;
  messages_count: number;
  diagnostic_stage: string;
}

function apiBase(): string {
  return getApiBaseUrl().replace(/\/$/, "");
}

export async function fetchActiveDiagnosticCards(
  sessionId?: string,
): Promise<DiagnosticCard[]> {
  const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  const res = await fetch(`${apiBase()}/api/v1/diagnostic-cards${query}`);
  if (!res.ok) {
    throw new Error(`Failed to load diagnostic cards (${res.status})`);
  }
  const data = (await res.json()) as { cards?: DiagnosticCard[] };
  return data.cards ?? [];
}

export async function fetchDiagnosticCard(cardId: string): Promise<{
  card: DiagnosticCard;
  conversation: DiagnosticMessage[];
  summary: DiagnosticCardSummary;
}> {
  const res = await fetch(`${apiBase()}/api/v1/diagnostic-cards/${cardId}`);
  if (!res.ok) {
    throw new Error(`Failed to load diagnostic card (${res.status})`);
  }
  return res.json();
}

export async function archiveDiagnosticCard(
  cardId: string,
  payload: { outcome: string; final_diagnosis: string; solution: string },
): Promise<void> {
  const res = await fetch(`${apiBase()}/api/v1/diagnostic-cards/${cardId}/archive`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to archive diagnostic card (${res.status})`);
  }
}

export async function createDiagnosticCard(payload: {
  device_id: string;
  device_name: string;
  session_id: string;
}): Promise<{ id: string; status: string }> {
  const res = await fetch(`${apiBase()}/api/v1/diagnostic-cards`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to create diagnostic card (${res.status})`);
  }
  return res.json();
}
