import type { DeviceKind } from "../types";
import { getApiBaseUrl, isLoopbackHost } from "../config/env";

const SESSION_KEY = "alpilab.session_id";
const DEVICE_KEY = "alpilab.device_id";
const DEVICE_TYPE_KEY = "alpilab.device_type";
const DEVICE_NAME_KEY = "alpilab.device_name";
const PAIRING_TOKEN_KEY = "alpilab.pairing_token";

const DEFAULT_SESSION_ID = "repair-001";

function detectDeviceType(): DeviceKind {
  if (typeof window === "undefined") return "pc";
  const ua = navigator.userAgent.toLowerCase();
  if (/ipad|tablet/.test(ua)) return "tablet";
  if (/iphone|android|mobile/.test(ua)) return "phone";
  return "pc";
}

function detectDeviceName(type: DeviceKind): string {
  if (type === "phone") return "Phone";
  if (type === "tablet") return "Tablet";
  return "PC";
}

function createId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID().slice(0, 8);
  }
  return Math.random().toString(16).slice(2, 10);
}

/** Pairing client_id is the WebSocket device_id. Stable across app restarts. */
export function loadOrCreateDeviceId(): string {
  const existing = localStorage.getItem(DEVICE_KEY);
  if (existing) return existing;
  const id = `device-${createId()}`;
  localStorage.setItem(DEVICE_KEY, id);
  return id;
}

export function saveDeviceId(deviceId: string): void {
  localStorage.setItem(DEVICE_KEY, deviceId);
}

export function loadPairingToken(): string | null {
  if (typeof window === "undefined") return null;
  const stored = localStorage.getItem(PAIRING_TOKEN_KEY);
  return stored ? stored : null;
}

export function savePairingToken(token: string): void {
  localStorage.setItem(PAIRING_TOKEN_KEY, token);
}

export function savePairedIdentity(opts: {
  deviceId: string;
  pairingToken: string;
  deviceType?: DeviceKind;
  deviceName?: string;
  sessionId?: string;
}): void {
  saveDeviceId(opts.deviceId);
  savePairingToken(opts.pairingToken);
  if (opts.deviceType) {
    localStorage.setItem(DEVICE_TYPE_KEY, opts.deviceType);
  }
  if (opts.deviceName) {
    localStorage.setItem(DEVICE_NAME_KEY, opts.deviceName);
  }
  if (opts.sessionId) {
    saveSessionId(opts.sessionId);
  }
}

export function loadDeviceType(): DeviceKind {
  if (typeof window !== "undefined" && isLoopbackHost(window.location.hostname)) {
    return "pc";
  }
  const stored = localStorage.getItem(DEVICE_TYPE_KEY) as DeviceKind | null;
  if (stored === "pc" || stored === "phone" || stored === "tablet") return stored;
  const detected = detectDeviceType();
  localStorage.setItem(DEVICE_TYPE_KEY, detected);
  return detected;
}

export function loadDeviceName(type: DeviceKind): string {
  return localStorage.getItem(DEVICE_NAME_KEY) || detectDeviceName(type);
}

export function saveSessionId(sessionId: string): void {
  localStorage.setItem(SESSION_KEY, sessionId);
}

/** Session comes from Hub/SQLite (or prior Hub bootstrap), never from ?session=. */
export function loadSessionId(): string {
  const stored = localStorage.getItem(SESSION_KEY);
  if (stored) return stored;
  saveSessionId(DEFAULT_SESSION_ID);
  return DEFAULT_SESSION_ID;
}

export async function resolveSessionIdFromHub(): Promise<string> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/api/v1/hub/info`);
    if (res.ok) {
      const data = (await res.json()) as { default_session_id?: string };
      const id = String(data.default_session_id || "").trim() || DEFAULT_SESSION_ID;
      saveSessionId(id);
      return id;
    }
  } catch {
    /* Hub unavailable — keep stored default */
  }
  return loadSessionId();
}

export function isPcLoopbackUi(): boolean {
  return typeof window !== "undefined" && isLoopbackHost(window.location.hostname);
}

export function clearSessionStorage(): void {
  localStorage.removeItem(SESSION_KEY);
}

export { PAIRING_TOKEN_KEY, DEVICE_KEY, SESSION_KEY, DEFAULT_SESSION_ID };
