import { describe, expect, it } from "vitest";
import { backendHttpFromLocation, httpToWs } from "../config/env";

describe("LAN backend URL resolution", () => {
  it("maps hotspot IP on Vite :5173 to backend :8000", () => {
    expect(backendHttpFromLocation("10.199.166.128", "5173", "http:")).toBe(
      "http://10.199.166.128:8000",
    );
    expect(httpToWs("http://10.199.166.128:8000")).toBe("ws://10.199.166.128:8000");
  });

  it("keeps same origin when UI is served from :8000", () => {
    expect(backendHttpFromLocation("10.199.166.128", "8000", "http:")).toBe(
      "http://10.199.166.128:8000",
    );
  });

  it("keeps loopback on default API", () => {
    expect(backendHttpFromLocation("localhost", "5173", "http:")).toBe(
      "http://127.0.0.1:8000",
    );
  });
});
