import { describe, it, expect, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { useRealtimeClient } from "../hooks/useRealtimeClient";
import type { RealtimeClient } from "../realtime/RealtimeClient";
describe("useRealtimeClient", () => {
  it("sends immediately when connected", () => {
    const send = vi.fn();
    const client = { send } as unknown as RealtimeClient;
    const clientRef = { current: client };
    const addToQueue = vi.fn();

    const { result } = renderHook(() =>
      useRealtimeClient({
        clientRef,
        canSend: true,
        addToQueue,
      }),
    );

    const ok = result.current.send({
      type: "chat_message",
      content: "Ciao",
      role: "user",
    });

    expect(ok).toBe(true);
    expect(send).toHaveBeenCalledTimes(1);
    expect(addToQueue).not.toHaveBeenCalled();
  });

  it("queues chat messages when offline", () => {
    const clientRef = { current: null as RealtimeClient | null };
    const addToQueue = vi.fn().mockReturnValue("queued-1");

    const { result } = renderHook(() =>
      useRealtimeClient({
        clientRef,
        canSend: false,
        addToQueue,
      }),
    );

    const ok = result.current.send({
      type: "chat_message",
      content: "Offline",
      role: "user",
    });

    expect(ok).toBe(false);
    expect(addToQueue).toHaveBeenCalledWith({
      type: "CHAT_MESSAGE",
      payload: {
        type: "chat_message",
        content: "Offline",
        role: "user",
      },
    });
  });
});
