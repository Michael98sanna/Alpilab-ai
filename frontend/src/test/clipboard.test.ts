import { describe, it, expect, vi } from "vitest";
import {
  writeClipboardText,
  readClipboardText,
  getDomSelectionText,
} from "../utils/clipboard";

describe("clipboard helpers", () => {
  it("writeClipboardText uses navigator.clipboard", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText, readText: vi.fn() },
    });
    await expect(writeClipboardText("hello")).resolves.toBe(true);
    expect(writeText).toHaveBeenCalledWith("hello");
    vi.unstubAllGlobals();
  });

  it("writeClipboardText rejects empty string without writing", async () => {
    const writeText = vi.fn();
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText, readText: vi.fn() },
    });
    await expect(writeClipboardText("")).resolves.toBe(false);
    expect(writeText).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("readClipboardText returns clipboard contents", async () => {
    const readText = vi.fn().mockResolvedValue("from-clip");
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText: vi.fn(), readText },
    });
    await expect(readClipboardText()).resolves.toBe("from-clip");
    vi.unstubAllGlobals();
  });

  it("getDomSelectionText returns empty when no selection", () => {
    expect(getDomSelectionText()).toBe("");
  });
});
