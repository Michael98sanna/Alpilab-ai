export type AppMode = "mock" | "realtime";

export type ConnectionState =
  | "CONNECTING"
  | "CONNECTED"
  | "DISCONNECTED"
  | "RECONNECTING"
  | "ERROR"
  | "UNAUTHORIZED";

const DEFAULT_WS = "ws://127.0.0.1:8000";
const DEFAULT_API = "http://127.0.0.1:8000";
const BACKEND_PORT = "8000";
const VITE_DEV_PORT = "5173";

function isBrowser(): boolean {
  return typeof window !== "undefined" && Boolean(window.location);
}

export function isLoopbackHost(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]";
}

export function isViteDevPort(port: string): boolean {
  return port === VITE_DEV_PORT;
}

export function hubOriginFromLocation(
  hostname: string,
  port: string,
  protocol: string,
): string {
  const httpProto = protocol === "https:" ? "https:" : "http:";
  if (!port) {
    return `${httpProto}//${hostname}`;
  }
  return `${httpProto}//${hostname}:${port}`;
}

export function backendHttpFromLocation(
  hostname: string,
  port: string,
  protocol: string,
): string {
  const httpProto = protocol === "https:" ? "https:" : "http:";
  if (isLoopbackHost(hostname)) {
    return DEFAULT_API;
  }
  if (!port || port === BACKEND_PORT) {
    return `${httpProto}//${hostname}${port ? `:${port}` : ""}`;
  }
  return `${httpProto}//${hostname}:${BACKEND_PORT}`;
}

export function httpToWs(httpUrl: string): string {
  if (httpUrl.startsWith("https://")) {
    return `wss://${httpUrl.slice("https://".length)}`;
  }
  if (httpUrl.startsWith("http://")) {
    return `ws://${httpUrl.slice("http://".length)}`;
  }
  return DEFAULT_WS;
}

export function resolveBackendHttpUrl(): string {
  if (!isBrowser()) {
    return import.meta.env.VITE_API_URL || DEFAULT_API;
  }
  const { hostname, port, protocol } = window.location;
  // Vite dev only. EXE / Local Hub UI must use the page origin, never a baked
  // VITE_WS_URL (tunnel/cloudflare leftover in frontend/dist).
  if (isViteDevPort(port)) {
    return backendHttpFromLocation(hostname, port, protocol);
  }
  return hubOriginFromLocation(hostname, port, protocol);
}

export function resolveBackendWsUrl(): string {
  return httpToWs(resolveBackendHttpUrl());
}

export function getAppMode(): AppMode {
  const mode = import.meta.env.VITE_APP_MODE?.toLowerCase();
  if (mode === "mock") return "mock";
  return "realtime";
}

export function getApiBaseUrl(): string {
  return resolveBackendHttpUrl();
}

export function getWsBaseUrl(): string {
  return resolveBackendWsUrl();
}

export function getSessionIdFromUrl(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("session");
}
