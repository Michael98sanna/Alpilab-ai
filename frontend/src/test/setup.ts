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
