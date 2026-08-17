export type AppMode = "mock" | "realtime";

export type ConnectionState =
  | "CONNECTING"
  | "CONNECTED"
  | "DISCONNECTED"
  | "RECONNECTING"
  | "ERROR";

const DEFAULT_WS = "ws://127.0.0.1:8000";
const DEFAULT_API = "http://127.0.0.1:8000";

export function getAppMode(): AppMode {
  const mode = import.meta.env.VITE_APP_MODE?.toLowerCase();
  return mode === "realtime" ? "realtime" : "mock";
}

export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_URL || DEFAULT_API;
}

export function getWsBaseUrl(): string {
  return import.meta.env.VITE_WS_URL || DEFAULT_WS;
}

export function getSessionIdFromUrl(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("session");
}
