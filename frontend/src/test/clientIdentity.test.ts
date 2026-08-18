import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  DEFAULT_SESSION_ID,
  DEVICE_KEY,
  SESSION_KEY,
  loadOrCreateDeviceId,
  loadPairingToken,
  loadSessionId,
  savePairedIdentity,
} from "../realtime/sessionStorage";

describe("client identity", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("keeps a stable device_id across reloads", () => {
    const first = loadOrCreateDeviceId();
    const second = loadOrCreateDeviceId();
    expect(first).toBe(second);
    expect(localStorage.getItem(DEVICE_KEY)).toBe(first);
  });

  it("pairing identity is the WebSocket device_id and persists token", () => {
    savePairedIdentity({
      deviceId: "phone-stable-01",
      pairingToken: "secret-token",
      deviceType: "phone",
      sessionId: "repair-001",
    });
    expect(loadOrCreateDeviceId()).toBe("phone-stable-01");
    expect(loadPairingToken()).toBe("secret-token");
    expect(loadSessionId()).toBe("repair-001");
  });

  it("does not take session from ?session= URL", () => {
    window.history.replaceState({}, "", "/?session=other-session");
    localStorage.removeItem(SESSION_KEY);
    expect(loadSessionId()).toBe(DEFAULT_SESSION_ID);
    expect(loadSessionId()).not.toBe("other-session");
  });
});
