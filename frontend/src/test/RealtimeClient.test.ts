import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { RealtimeClient } from "../realtime/RealtimeClient";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  readyState = 0;
  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }

  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = 3;
    this.onclose?.();
  });

  simulateOpen() {
    this.readyState = 1;
    this.onopen?.();
  }

  simulateMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  simulateClose() {
    this.readyState = 3;
    this.onclose?.();
  }
}

describe("RealtimeClient", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    MockWebSocket.instances = [];
    vi.stubGlobal(
      "WebSocket",
      Object.assign(MockWebSocket, { OPEN: 1, CONNECTING: 0, CLOSING: 2, CLOSED: 3 }),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("connects and receives snapshot", () => {
    const onMessage = vi.fn();
    const onConnectionChange = vi.fn();
    const client = new RealtimeClient({
      sessionId: "repair-1",
      deviceId: "pc-1",
      deviceType: "pc",
      deviceName: "PC",
      onMessage,
      onConnectionChange,
    });
    client.connect();
    expect(onConnectionChange).toHaveBeenCalledWith("CONNECTING");
    MockWebSocket.instances[0].simulateOpen();
    expect(onConnectionChange).toHaveBeenCalledWith("CONNECTED");
    MockWebSocket.instances[0].simulateMessage({
      type: "snapshot",
      payload: { session: { id: "repair-1" } },
    });
    expect(onMessage).toHaveBeenCalled();
  });

  it("sends chat message when connected", () => {
    const client = new RealtimeClient({
      sessionId: "repair-1",
      deviceId: "pc-1",
      deviceType: "pc",
      deviceName: "PC",
      onMessage: vi.fn(),
      onConnectionChange: vi.fn(),
    });
    client.connect();
    MockWebSocket.instances[0].simulateOpen();
    client.send({ type: "chat_message", content: "Test", role: "user" });
    expect(MockWebSocket.instances[0].send).toHaveBeenCalled();
  });

  it("sends pairing_token from client identity, not from the page URL", () => {
    window.history.replaceState({}, "", "/?pairing_token=from-url&session=other");
    const client = new RealtimeClient({
      sessionId: "repair-001",
      deviceId: "phone-stable-01",
      deviceType: "phone",
      deviceName: "Android",
      pairingToken: "stored-token",
      onMessage: vi.fn(),
      onConnectionChange: vi.fn(),
    });
    client.connect();
    const url = MockWebSocket.instances[0].url;
    expect(url).toContain("/ws/sessions/repair-001");
    expect(url).toContain("device_id=phone-stable-01");
    expect(url).toContain("pairing_token=stored-token");
    expect(url).not.toContain("from-url");
    expect(url).not.toContain("other");
  });

  it("enters UNAUTHORIZED state and stops reconnect on auth errors", () => {
    const onConnectionChange = vi.fn();
    const client = new RealtimeClient({
      sessionId: "repair-001",
      deviceId: "phone-1",
      deviceType: "phone",
      deviceName: "Android",
      pairingToken: "revoked-token",
      onMessage: vi.fn(),
      onConnectionChange,
    });
    client.connect();
    MockWebSocket.instances[0].simulateOpen();
    MockWebSocket.instances[0].simulateMessage({
      type: "error",
      message: "UNAUTHORIZED",
    });
    expect(onConnectionChange).toHaveBeenCalledWith("UNAUTHORIZED");
    expect(onConnectionChange).not.toHaveBeenCalledWith("RECONNECTING");
  });

  it("reconnects after connection loss and receives snapshot again", () => {
    const onMessage = vi.fn();
    const onConnectionChange = vi.fn();
    const client = new RealtimeClient({
      sessionId: "repair-001",
      deviceId: "phone-1",
      deviceType: "phone",
      deviceName: "Android",
      pairingToken: "stored-token",
      onMessage,
      onConnectionChange,
    });
    client.connect();
    const first = MockWebSocket.instances[0];
    first.simulateOpen();
    first.simulateClose();
    expect(onConnectionChange).toHaveBeenCalledWith("RECONNECTING");
    vi.advanceTimersByTime(1000);
    const second = MockWebSocket.instances[1];
    second.simulateOpen();
    second.simulateMessage({ type: "snapshot", payload: { session: { id: "repair-001" } } });
    expect(onConnectionChange).toHaveBeenCalledWith("CONNECTED");
    expect(onMessage).toHaveBeenCalled();
  });
});
