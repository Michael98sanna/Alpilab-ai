import { getApiBaseUrl } from "../config/env";
import type { OpenableToolId } from "../programs/catalog";

export interface ToolExecuteResult {
  success: boolean;
  toolId: string;
  error: string | null;
  result: Record<string, unknown>;
}

/**
 * Execute a pre-registered Hub tool via the existing REST path
 * (Authorization + ToolRegistry + AgentGateway + PC Agent).
 */
export async function executeRegisteredTool(
  sessionId: string,
  agentId: string,
  toolId: OpenableToolId | "demo.safe_test",
): Promise<ToolExecuteResult> {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const url =
    `${base}/api/v1/sessions/${encodeURIComponent(sessionId)}` +
    `/agents/${encodeURIComponent(agentId)}` +
    `/tools/${encodeURIComponent(toolId)}/execute`;

  const response = await fetch(url, { method: "POST" });
  if (!response.ok) {
    return {
      success: false,
      toolId,
      error: `HTTP_${response.status}`,
      result: {},
    };
  }
  const body = (await response.json()) as {
    success?: boolean;
    tool_id?: string;
    error?: string | null;
    result?: Record<string, unknown>;
  };
  return {
    success: Boolean(body.success),
    toolId: body.tool_id || toolId,
    error: body.error ?? null,
    result: body.result ?? {},
  };
}
