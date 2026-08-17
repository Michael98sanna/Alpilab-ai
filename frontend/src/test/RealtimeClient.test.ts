import { describe, it, expect, vi, beforeEach } from "vitest";
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
}

describe("RealtimeClient", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal(
      "WebSocket",
      Object.assign(MockWebSocket, { OPEN: 1, CONNECTING: 0, CLOSING: 2, CLOSED: 3 }),
    );
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
});
