import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

vi.stubGlobal(
  "fetch",
  vi.fn().mockImplementation((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/diagnostic-cards/") && !url.endsWith("/diagnostic-cards")) {
      return Promise.resolve({
        ok: true,
        json: async () => ({
          card: {
            id: "card-1",
            device_name: "Test",
            device_id: "dev-1",
            status: "active",
            confidence: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            diagnostic_stage: "intake",
          },
          conversation: [],
          summary: {
            device: "Test",
            status: "active",
            started: new Date().toISOString(),
            updated: new Date().toISOString(),
            confidence: 0,
            messages_count: 0,
            diagnostic_stage: "intake",
          },
        }),
      });
    }
    if (url.includes("/diagnostic-cards")) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ cards: [] }),
      });
    }
    if (url.includes("/api/v1/ai/metrics/providers")) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ providers: [] }),
      });
    }
    if (url.includes("/api/v1/ai/providers/status")) {
      return Promise.resolve({
        ok: true,
        json: async () => ({
          providers: [],
          online_available: false,
          offline_mode: true,
          kb: { mode: "disabled", model_name: null, indexed_cases: 0 },
        }),
      });
    }
    if (url.includes("/api/v1/ai/metrics")) {
      return Promise.resolve({
        ok: true,
        json: async () => ({
          global_accuracy: 0,
          by_type: [],
          kb_maturity: {
            indexed_cases: 0,
            cases_by_type: {},
            local_hit_rate_30d: 0,
            estimated_api_calls_saved: 0,
            maturity_stage: "cold",
          },
        }),
      });
    }
    return Promise.resolve({
      ok: true,
      json: async () => ({ default_session_id: "repair-001", code: "123456" }),
    });
  }),
);

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: query.includes("1024px") ? false : false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
