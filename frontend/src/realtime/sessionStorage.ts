import type { DeviceKind } from "../types";

const SESSION_KEY = "alpilab.session_id";
const DEVICE_KEY = "alpilab.device_id";
const DEVICE_TYPE_KEY = "alpilab.device_type";
const DEVICE_NAME_KEY = "alpilab.device_name";

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

export function loadOrCreateDeviceId(): string {
  const existing = localStorage.getItem(DEVICE_KEY);
  if (existing) return existing;
  const id = `device-${crypto.randomUUID().slice(0, 8)}`;
  localStorage.setItem(DEVICE_KEY, id);
  return id;
}

export function loadDeviceType(): DeviceKind {
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

export function loadSessionId(fallback?: string | null): string {
  const fromUrl = fallback ?? null;
  if (fromUrl) {
    saveSessionId(fromUrl);
    return fromUrl;
  }
  const stored = localStorage.getItem(SESSION_KEY);
  if (stored) return stored;
  const generated = `repair-${crypto.randomUUID().slice(0, 8)}`;
  saveSessionId(generated);
  return generated;
}

export function clearSessionStorage(): void {
  localStorage.removeItem(SESSION_KEY);
}
