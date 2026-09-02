import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useRepairCards } from "../hooks/useRepairCards";

vi.mock("../config/env", () => ({
  getApiBaseUrl: () => "http://127.0.0.1:8000",
}));

describe("useRepairCards sendCardMessage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/ai/chat")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              content: "Risposta Brain di test",
              provider: "mock",
              model: "mock",
              source: "online",
              confidence: 0.8,
              task_type: "diagnosis",
              similar_cases_count: 0,
              similar_cases: [],
              kb_hits: 0,
              used_online: true,
              latency_ms: 12,
              low_accuracy_warning: false,
            }),
          });
        }
        if (url.includes("/diagnostic-cards/") && !url.endsWith("/diagnostic-cards")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              card: {
                id: "card-1",
                device_name: "iPhone 13",
                device_id: "iphone-13",
                status: "active",
                confidence: 0,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                diagnostic_stage: "intake",
              },
              conversation: [
                {
                  role: "user",
                  content: "Display nero",
                  timestamp: new Date().toISOString(),
                },
                {
                  role: "assistant",
                  content: "Risposta Brain di test",
                  timestamp: new Date().toISOString(),
                },
              ],
              summary: {
                device: "iPhone 13",
                status: "active",
                started: new Date().toISOString(),
                updated: new Date().toISOString(),
                confidence: 0.8,
                messages_count: 2,
                diagnostic_stage: "hypothesis",
              },
            }),
          });
        }
        if (url.includes("/diagnostic-cards")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              cards: [
                {
                  id: "card-1",
                  session_id: "repair-001",
                  device_name: "iPhone 13",
                  device_id: "iphone-13",
                  status: "active",
                  confidence: 0,
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString(),
                  diagnostic_stage: "intake",
                },
              ],
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );
  });

  it("shows the user message immediately and loads card conversation", async () => {
    const { result } = renderHook(() => useRepairCards("repair-001", "card-1"));

    await waitFor(() => {
      expect(result.current.cards).toHaveLength(1);
    });

    await act(async () => {
      await result.current.sendCardMessage("card-1", "Display nero");
    });

    expect(result.current.cardMessages.some((message) => message.content === "Display nero")).toBe(
      true,
    );
    expect(
      result.current.cardMessages.some((message) => message.content === "Risposta Brain di test"),
    ).toBe(true);
  });
});
