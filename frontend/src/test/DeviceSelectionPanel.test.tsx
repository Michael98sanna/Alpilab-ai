import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DeviceSelectionPanel } from "../components/repair/DeviceSelectionPanel";
import type { DetectedDevice, DeviceContext } from "../types";

const mockDevice = (id: string, brand = "Samsung", model = "Galaxy S24"): DetectedDevice => ({
  id,
  brand,
  model,
  variant: null,
  serial_number: id,
  connection_type: "usb",
  source: "adb",
  detected_at: new Date().toISOString(),
});

const mockContext = (id: string, brand = "Samsung", model = "Galaxy S24"): DeviceContext => ({
  id,
  brand,
  model,
  serial_number: id,
  connection_type: "usb",
  source: "adb",
  associated_at: new Date().toISOString(),
});

// ---------------------------------------------------------------------------
// 1. Zero devices
// ---------------------------------------------------------------------------

describe("DeviceSelectionPanel — 0 devices", () => {
  it("renders nothing when no devices and no context", () => {
    const { container } = render(
      <DeviceSelectionPanel
        detectedDevices={[]}
        deviceContext={null}
        onAssociate={vi.fn()}
        onUnassociate={vi.fn()}
        onDismiss={vi.fn()}
      />,
    );
    expect(container.firstChild).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 2. One device
// ---------------------------------------------------------------------------

describe("DeviceSelectionPanel — 1 device", () => {
  it("renders detected section with one device", () => {
    render(
      <DeviceSelectionPanel
        detectedDevices={[mockDevice("adb-A")]}
        deviceContext={null}
        onAssociate={vi.fn()}
        onUnassociate={vi.fn()}
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByTestId("device-selection-panel")).toBeTruthy();
    expect(screen.getByTestId("detected-devices-section")).toBeTruthy();
    expect(screen.getByTestId("detected-device-adb-A")).toBeTruthy();
    expect(screen.getByText(/dispositivo rilevato/i)).toBeTruthy();
  });

  it("shows Associa and Ignora buttons", () => {
    render(
      <DeviceSelectionPanel
        detectedDevices={[mockDevice("adb-A")]}
        deviceContext={null}
        onAssociate={vi.fn()}
        onUnassociate={vi.fn()}
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByTestId("associate-btn-adb-A")).toBeTruthy();
    expect(screen.getByTestId("dismiss-btn")).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 3. Multiple devices
// ---------------------------------------------------------------------------

describe("DeviceSelectionPanel — N devices", () => {
  it("renders all detected devices", () => {
    render(
      <DeviceSelectionPanel
        detectedDevices={[mockDevice("adb-A"), mockDevice("adb-B", "Apple", "iPhone 14")]}
        deviceContext={null}
        onAssociate={vi.fn()}
        onUnassociate={vi.fn()}
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByTestId("detected-device-adb-A")).toBeTruthy();
    expect(screen.getByTestId("detected-device-adb-B")).toBeTruthy();
    expect(screen.getByText(/dispositivi rilevati/i)).toBeTruthy();
  });

  it("shows individual Associate buttons per device", () => {
    render(
      <DeviceSelectionPanel
        detectedDevices={[mockDevice("adb-A"), mockDevice("adb-B", "Apple", "iPhone 14")]}
        deviceContext={null}
        onAssociate={vi.fn()}
        onUnassociate={vi.fn()}
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByTestId("associate-btn-adb-A")).toBeTruthy();
    expect(screen.getByTestId("associate-btn-adb-B")).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 4. Association
// ---------------------------------------------------------------------------

describe("DeviceSelectionPanel — association", () => {
  it("calls onAssociate with correct id", () => {
    const onAssociate = vi.fn();
    render(
      <DeviceSelectionPanel
        detectedDevices={[mockDevice("adb-A")]}
        deviceContext={null}
        onAssociate={onAssociate}
        onUnassociate={vi.fn()}
        onDismiss={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId("associate-btn-adb-A"));
    expect(onAssociate).toHaveBeenCalledWith("adb-A");
  });
});

// ---------------------------------------------------------------------------
// 5. Device context already set
// ---------------------------------------------------------------------------

describe("DeviceSelectionPanel — device context present", () => {
  it("shows associated section with device name", () => {
    render(
      <DeviceSelectionPanel
        detectedDevices={[]}
        deviceContext={mockContext("adb-A")}
        onAssociate={vi.fn()}
        onUnassociate={vi.fn()}
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByTestId("device-context")).toBeTruthy();
    expect(screen.getByText(/dispositivo della riparazione/i)).toBeTruthy();
    expect(screen.getByTestId("unassociate-btn")).toBeTruthy();
  });

  it("shows associated badge when device is in detected list and associated", () => {
    render(
      <DeviceSelectionPanel
        detectedDevices={[mockDevice("adb-A")]}
        deviceContext={mockContext("adb-A")}
        onAssociate={vi.fn()}
        onUnassociate={vi.fn()}
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByTestId("associated-badge")).toBeTruthy();
    expect(screen.queryByTestId("associate-btn-adb-A")).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 6. Disassociation
// ---------------------------------------------------------------------------

describe("DeviceSelectionPanel — disassociation", () => {
  it("calls onUnassociate when Rimuovi clicked", () => {
    const onUnassociate = vi.fn();
    render(
      <DeviceSelectionPanel
        detectedDevices={[]}
        deviceContext={mockContext("adb-A")}
        onAssociate={vi.fn()}
        onUnassociate={onUnassociate}
        onDismiss={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId("unassociate-btn"));
    expect(onUnassociate).toHaveBeenCalledOnce();
  });
});

// ---------------------------------------------------------------------------
// 7. Dismiss
// ---------------------------------------------------------------------------

describe("DeviceSelectionPanel — dismiss", () => {
  it("calls onDismiss when Ignora clicked", () => {
    const onDismiss = vi.fn();
    render(
      <DeviceSelectionPanel
        detectedDevices={[mockDevice("adb-A")]}
        deviceContext={null}
        onAssociate={vi.fn()}
        onUnassociate={vi.fn()}
        onDismiss={onDismiss}
      />,
    );
    fireEvent.click(screen.getByTestId("dismiss-btn"));
    expect(onDismiss).toHaveBeenCalledOnce();
  });

  it("no Ignora button when context is already set", () => {
    render(
      <DeviceSelectionPanel
        detectedDevices={[mockDevice("adb-A")]}
        deviceContext={mockContext("adb-A")}
        onAssociate={vi.fn()}
        onUnassociate={vi.fn()}
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.queryByTestId("dismiss-btn")).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 8. ADB state tag (unauthorized)
// ---------------------------------------------------------------------------

describe("DeviceSelectionPanel — ADB state", () => {
  it("shows unauthorized state tag", () => {
    const dev: DetectedDevice = {
      ...mockDevice("adb-X"),
      metadata: { adb_state: "unauthorized" },
    };
    render(
      <DeviceSelectionPanel
        detectedDevices={[dev]}
        deviceContext={null}
        onAssociate={vi.fn()}
        onUnassociate={vi.fn()}
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByTestId("adb-state")).toBeTruthy();
    expect(screen.getByTestId("adb-state").textContent).toBe("unauthorized");
  });
});

// ---------------------------------------------------------------------------
// 9. mapEvents: REPAIR_DEVICE_* actions
// ---------------------------------------------------------------------------

import { mapRealtimeEventToActions } from "../realtime/mapEvents";
import type { RealtimeEventEnvelope } from "../realtime/types";

function makeEvent(event_type: string, payload: Record<string, unknown>): RealtimeEventEnvelope {
  return { id: "evt-1", repair_session_id: "s1", event_type, payload };
}

describe("mapEvents — REPAIR_DEVICE_*", () => {
  it("REPAIR_DEVICE_LIST_UPDATED dispatches SET_DETECTED_DEVICES", () => {
    const actions = mapRealtimeEventToActions(makeEvent("REPAIR_DEVICE_LIST_UPDATED", {
      detected_devices: [{ id: "adb-A", brand: "Samsung", model: "Galaxy S24" }],
    }));
    expect(actions).toHaveLength(1);
    expect(actions[0].type).toBe("SET_DETECTED_DEVICES");
  });

  it("REPAIR_DEVICE_DETECTED dispatches SET_DETECTED_DEVICES", () => {
    const actions = mapRealtimeEventToActions(makeEvent("REPAIR_DEVICE_DETECTED", {
      detected_devices: [],
    }));
    expect(actions[0].type).toBe("SET_DETECTED_DEVICES");
  });

  it("REPAIR_DEVICE_ASSOCIATED dispatches SET_DEVICE_CONTEXT", () => {
    const actions = mapRealtimeEventToActions(makeEvent("REPAIR_DEVICE_ASSOCIATED", {
      id: "adb-A",
      brand: "Samsung",
      model: "Galaxy S24",
    }));
    expect(actions[0].type).toBe("SET_DEVICE_CONTEXT");
  });

  it("REPAIR_DEVICE_UNASSOCIATED dispatches SET_DEVICE_CONTEXT null", () => {
    const actions = mapRealtimeEventToActions(makeEvent("REPAIR_DEVICE_UNASSOCIATED", {}));
    expect(actions[0].type).toBe("SET_DEVICE_CONTEXT");
    if (actions[0].type === "SET_DEVICE_CONTEXT") {
      expect(actions[0].context).toBeNull();
    }
  });

  it("REPAIR_DEVICE_DISCONNECTED produces no actions (context preserved)", () => {
    const actions = mapRealtimeEventToActions(makeEvent("REPAIR_DEVICE_DISCONNECTED", {}));
    expect(actions).toHaveLength(0);
  });
});
