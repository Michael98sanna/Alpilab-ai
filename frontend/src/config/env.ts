export type AppMode = "mock" | "realtime";

export type ConnectionState =
  | "CONNECTING"
  | "CONNECTED"
  | "DISCONNECTED"
  | "RECONNECTING"
  | "ERROR";

const DEFAULT_WS = "ws://127.0.0.1:8000";
const DEFAULT_API = "http://127.0.0.1:8000";
const BACKEND_PORT = "8000";

function isBrowser(): boolean {
  return typeof window !== "undefined" && Boolean(window.location);
}

export function isLoopbackHost(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]";
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
  if (isLoopbackHost(window.location.hostname)) {
    return import.meta.env.VITE_API_URL || DEFAULT_API;
  }
  return backendHttpFromLocation(
    window.location.hostname,
    window.location.port,
    window.location.protocol,
  );
}

export function resolveBackendWsUrl(): string {
  return httpToWs(resolveBackendHttpUrl());
}

export function getAppMode(): AppMode {
  const mode = import.meta.env.VITE_APP_MODE?.toLowerCase();
  return mode === "realtime" ? "realtime" : "mock";
}

export function getApiBaseUrl(): string {
  if (getAppMode() === "realtime" && isBrowser() && !isLoopbackHost(window.location.hostname)) {
    return resolveBackendHttpUrl();
  }
  return import.meta.env.VITE_API_URL || DEFAULT_API;
}

export function getWsBaseUrl(): string {
  if (getAppMode() === "realtime" && isBrowser() && !isLoopbackHost(window.location.hostname)) {
    return resolveBackendWsUrl();
  }
  return import.meta.env.VITE_WS_URL || DEFAULT_WS;
}

export function getSessionIdFromUrl(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("session");
}
