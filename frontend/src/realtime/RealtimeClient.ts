import { getWsBaseUrl } from "../config/env";
import type { ConnectionState } from "../config/env";
import type { OutboundMessage, RealtimeClientOptions, WsServerMessage } from "./types";

const MAX_RECONNECT_ATTEMPTS = 8;
const BASE_DELAY_MS = 1000;

export class RealtimeClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private closedIntentionally = false;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;

  constructor(private readonly options: RealtimeClientOptions) {}

  connect(): void {
    this.closedIntentionally = false;
    this.openSocket();
  }

  disconnect(): void {
    this.closedIntentionally = true;
    this.clearTimers();
    this.ws?.close();
    this.ws = null;
    this.options.onConnectionChange("DISCONNECTED");
  }

  send(message: OutboundMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket not connected");
    }
    this.ws.send(JSON.stringify(message));
  }

  private openSocket(): void {
    this.options.onConnectionChange(
      this.reconnectAttempts > 0 ? "RECONNECTING" : "CONNECTING",
    );

    const base = getWsBaseUrl().replace(/\/$/, "");
    const params = new URLSearchParams({
      device_id: this.options.deviceId,
      device_type: this.options.deviceType,
      device_name: this.options.deviceName,
    });
    if (this.options.seedDemo) {
      params.set("seed_demo", "true");
    }
    const token = this.options.pairingToken;
    if (token) {
      params.set("pairing_token", token);
    }
    const url = `${base}/ws/sessions/${encodeURIComponent(this.options.sessionId)}?${params}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.options.onConnectionChange("CONNECTED");
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(String(event.data)) as WsServerMessage;
        this.options.onMessage(data);
      } catch {
        this.options.onConnectionChange("ERROR");
      }
    };

    this.ws.onerror = () => {
      this.options.onConnectionChange("ERROR");
    };

    this.ws.onclose = () => {
      this.clearHeartbeat();
      if (this.closedIntentionally) {
        this.options.onConnectionChange("DISCONNECTED");
        return;
      }
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      this.options.onConnectionChange("ERROR");
      return;
    }
    this.options.onConnectionChange("RECONNECTING");
    const delay = BASE_DELAY_MS * 2 ** this.reconnectAttempts;
    this.reconnectAttempts += 1;
    this.reconnectTimer = setTimeout(() => this.openSocket(), delay);
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      try {
        this.send({ type: "heartbeat" });
      } catch {
        /* ignore */
      }
    }, 25000);
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private clearTimers(): void {
    this.clearHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

export type { ConnectionState };
