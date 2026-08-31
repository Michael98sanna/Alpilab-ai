import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type { ReactNode } from "react";
import { OfflineQueueProvider, useOfflineQueue } from "../hooks/useOfflineQueue";

vi.mock("../utils/offlineDb", () => ({
  loadQueueFromDb: vi.fn().mockResolvedValue([]),
  persistQueueItem: vi.fn().mockResolvedValue(undefined),
  clearSyncedQueueItems: vi.fn().mockResolvedValue(undefined),
  cacheResponse: vi.fn().mockResolvedValue(undefined),
  getCachedResponse: vi.fn().mockResolvedValue(null),
}));

function wrapper({ children }: { children: ReactNode }) {
  return <OfflineQueueProvider>{children}</OfflineQueueProvider>;
}

describe("useOfflineQueue", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window.navigator, "onLine", {
      configurable: true,
      value: true,
    });
  });

  it("adds actions to the queue", () => {
    const { result } = renderHook(() => useOfflineQueue(), { wrapper });

    act(() => {
      result.current.addToQueue({
        type: "CHAT_MESSAGE",
        payload: { content: "Ciao" },
      });
    });

    expect(result.current.queue).toHaveLength(1);
    expect(result.current.queue[0].status).toBe("pending");
  });

  it("syncs pending actions when send succeeds", async () => {
    const { result } = renderHook(() => useOfflineQueue(), { wrapper });
    const send = vi.fn().mockResolvedValue(undefined);

    act(() => {
      result.current.addToQueue({
        type: "CHAT_MESSAGE",
        payload: { content: "offline msg" },
      });
    });

    await act(async () => {
      await result.current.syncQueue(send);
    });

    expect(send).toHaveBeenCalledTimes(1);
    expect(result.current.queue[0].status).toBe("synced");
  });

  it("tracks offline state from navigator", () => {
    Object.defineProperty(window.navigator, "onLine", {
      configurable: true,
      value: false,
    });

    const { result } = renderHook(() => useOfflineQueue(), { wrapper });
    expect(result.current.isOnline).toBe(false);
  });

  it("syncs via registered handler after reconnect", async () => {
    const { result } = renderHook(() => useOfflineQueue(), { wrapper });
    const send = vi.fn().mockResolvedValue(undefined);

    act(() => {
      result.current.registerSyncHandler(send);
      result.current.addToQueue({
        type: "DIAGNOSTIC_UPDATE",
        payload: { test_id: "t1", value: "ok" },
      });
    });

    await act(async () => {
      await result.current.syncQueue(send);
    });

    expect(send).toHaveBeenCalledTimes(1);
  });
});
