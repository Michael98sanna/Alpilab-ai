import { describe, expect, it } from "vitest";
import { deviceLooksLikeIphone, hasIphoneConnected } from "./deviceKind";

describe("deviceKind", () => {
  it("detects iPhone from brand/model", () => {
    expect(deviceLooksLikeIphone({ brand: "Apple", model: "iPhone 14" })).toBe(true);
    expect(deviceLooksLikeIphone({ brand: "Samsung", model: "Galaxy S24" })).toBe(false);
  });

  it("shows panic panel only when an iPhone is connected", () => {
    expect(
      hasIphoneConnected(
        { id: "adb-1", brand: "Samsung", model: "Galaxy", associated_at: "" },
        [],
      ),
    ).toBe(false);
    expect(
      hasIphoneConnected(null, [
        { id: "usb-1", brand: "Apple", model: "iPhone 13", connection_type: "usb", source: "adb" },
      ]),
    ).toBe(true);
  });
});
