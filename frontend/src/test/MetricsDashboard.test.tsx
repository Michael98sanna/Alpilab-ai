import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MetricsDashboard } from "../components/ai/MetricsDashboard";

vi.mock("../config/env", () => ({
  getApiBaseUrl: () => "http://127.0.0.1:8000",
}));

describe("MetricsDashboard", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/ai/metrics/providers")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              diagnosis_type: "providers",
              accuracy: 0,
              total: 0,
            }),
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
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );
  });

  it("renders without crashing when provider metrics payload is malformed", async () => {
    render(<MetricsDashboard />);
    await waitFor(() => {
      expect(screen.getByTestId("brain-metrics-dashboard")).toBeInTheDocument();
    });
    expect(screen.getByText(/Formato metriche provider non valido/i)).toBeInTheDocument();
    expect(screen.getByText(/Nessun dato provider ancora/i)).toBeInTheDocument();
  });
});
