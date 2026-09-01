import type { DetectedDevice, DeviceContext } from "../types";

type DeviceLike = {
  brand?: string | null;
  model?: string | null;
  id?: string;
  source?: string | null;
};

export function deviceLooksLikeIphone(device: DeviceLike): boolean {
  const brand = (device.brand ?? "").toLowerCase();
  const model = (device.model ?? "").toLowerCase();
  const id = (device.id ?? "").toLowerCase();
  const source = (device.source ?? "").toLowerCase();

  return (
    brand.includes("apple") ||
    model.includes("iphone") ||
    id.includes("iphone") ||
    source === "idevice" ||
    source === "3utools"
  );
}

export function hasIphoneConnected(
  deviceContext: DeviceContext | null,
  detectedDevices: DetectedDevice[],
): boolean {
  if (deviceContext && deviceLooksLikeIphone(deviceContext)) {
    return true;
  }
  return detectedDevices.some(deviceLooksLikeIphone);
}

export function deviceDisplayName(
  brand: string | null | undefined,
  model: string | null | undefined,
  fallbackId: string,
): string {
  const label = [brand, model].filter(Boolean).join(" ");
  return label || fallbackId;
}
