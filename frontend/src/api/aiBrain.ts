import { getApiBaseUrl } from "../config/env";

export type BrainSource = "local_kb" | "hybrid" | "online";
export type KbMode = "semantic" | "hash" | "disabled";

export interface ValidationMeta {
  performed?: boolean;
  agreed?: boolean | null;
  overridden?: boolean;
}

export interface KbMaturity {
  indexed_cases: number;
  cases_by_type: Record<string, number>;
  local_hit_rate_30d: number;
  estimated_api_calls_saved: number;
  maturity_stage: "cold" | "warming" | "mature";
}

export interface BrainChatResponse {
  content: string;
  provider: string;
  model: string;
  source: BrainSource;
  confidence: number;
  task_type: string;
  similar_cases_count: number;
  similar_cases: Array<{
    id: string;
    diagnosis: string;
    similarity: number;
    confidence: number;
  }>;
  kb_hits: number;
  used_online: boolean;
  latency_ms: number;
  low_accuracy_warning: boolean;
  knowledge_entry_id?: string | null;
  kb_mode?: KbMode;
  strong_match?: boolean;
  validation?: ValidationMeta;
}

export interface BrainMetrics {
  global_accuracy?: number;
  by_type?: Array<{
    diagnosis_type: string;
    accuracy: number;
    total: number;
    correct: number;
  }>;
  diagnosis_type?: string;
  accuracy?: number;
  total?: number;
  kb_maturity?: KbMaturity;
}

function apiBase(): string {
  return getApiBaseUrl().replace(/\/$/, "");
}

export async function brainChat(
  cardId: string,
  message: string,
): Promise<BrainChatResponse> {
  const res = await fetch(`${apiBase()}/api/v1/ai/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ card_id: cardId, message }),
  });
  if (!res.ok) {
    let detail = "";
    try {
      const payload = (await res.json()) as { detail?: string | Array<{ msg?: string }> };
      if (typeof payload.detail === "string") {
        detail = payload.detail;
      } else if (Array.isArray(payload.detail)) {
        detail = payload.detail.map((item) => item.msg ?? "").filter(Boolean).join("; ");
      }
    } catch {
      /* ignore parse errors */
    }
    throw new Error(detail ? `Brain chat failed: ${detail}` : `Brain chat failed (${res.status})`);
  }
  return (await res.json()) as BrainChatResponse;
}

export async function submitBrainFeedback(
  cardId: string,
  payload: {
    feedback: "confirmed" | "corrected" | "rejected";
    correction_text?: string;
    provider?: string;
    pre_confidence?: number;
    knowledge_entry_id?: string | null;
  },
): Promise<{ confirmation_id: string }> {
  const res = await fetch(`${apiBase()}/api/v1/ai/cards/${cardId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Feedback failed (${res.status})`);
  }
  return (await res.json()) as { confirmation_id: string };
}

export async function submitRepairOutcome(
  confirmationId: string,
  outcome: "success" | "partial" | "failed",
  notes?: string,
): Promise<void> {
  const res = await fetch(`${apiBase()}/api/v1/ai/confirmations/${confirmationId}/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ outcome, notes }),
  });
  if (!res.ok) {
    throw new Error(`Outcome failed (${res.status})`);
  }
}

export async function fetchBrainMetrics(): Promise<BrainMetrics> {
  const res = await fetch(`${apiBase()}/api/v1/ai/metrics`);
  if (!res.ok) {
    throw new Error(`Metrics failed (${res.status})`);
  }
  return (await res.json()) as BrainMetrics;
}

export async function fetchProviderMetrics(): Promise<{
  providers: Array<{
    provider: string;
    diagnosis_type: string;
    accuracy: number;
    total: number;
    correct: number;
    avg_latency_ms: number;
  }>;
}> {
  const res = await fetch(`${apiBase()}/api/v1/ai/metrics/providers`);
  if (!res.ok) {
    throw new Error(`Provider metrics failed (${res.status})`);
  }
  return (await res.json()) as {
    providers: Array<{
      provider: string;
      diagnosis_type: string;
      accuracy: number;
      total: number;
      correct: number;
      avg_latency_ms: number;
    }>;
  };
}

export async function fetchProviderStatus(): Promise<{
  providers: Array<{ name: string; configured: boolean; healthy: boolean }>;
  online_available: boolean;
  offline_mode: boolean;
  kb?: {
    mode: KbMode;
    model_name: string | null;
    indexed_cases: number;
  };
}> {
  const res = await fetch(`${apiBase()}/api/v1/ai/providers/status`);
  if (!res.ok) {
    throw new Error(`Provider status failed (${res.status})`);
  }
  return (await res.json()) as {
    providers: Array<{ name: string; configured: boolean; healthy: boolean }>;
    online_available: boolean;
    offline_mode: boolean;
    kb?: {
      mode: KbMode;
      model_name: string | null;
      indexed_cases: number;
    };
  };
}
