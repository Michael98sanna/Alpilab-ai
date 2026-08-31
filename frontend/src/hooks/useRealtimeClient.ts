import { useCallback, type RefObject } from "react";
import type { RealtimeClient } from "../realtime/RealtimeClient";
import type { OutboundMessage } from "../realtime/types";
import type { QueuedAction, QueuedActionType } from "./useOfflineQueue";

function mapOutboundMessage(
  message: OutboundMessage,
): Omit<QueuedAction, "id" | "timestamp" | "status"> | null {
  switch (message.type) {
    case "chat_message":
      return { type: "CHAT_MESSAGE", payload: { ...message } };
    case "diagnostic_update":
      return { type: "DIAGNOSTIC_UPDATE", payload: { ...message } };
    case "associate_repair_device":
    case "unassociate_repair_device":
      return { type: "TOOL_EXECUTE", payload: { ...message } };
    case "heartbeat":
    case "request_snapshot":
      return null;
    default:
      return { type: "REALTIME_MESSAGE", payload: { ...message } };
  }
}

export interface UseRealtimeClientOptions {
  clientRef: RefObject<RealtimeClient | null>;
  canSend: boolean;
  addToQueue: (action: Omit<QueuedAction, "id" | "timestamp" | "status">) => string;
}

export function useRealtimeClient({
  clientRef,
  canSend,
  addToQueue,
}: UseRealtimeClientOptions) {
  const send = useCallback(
    (message: OutboundMessage): boolean => {
      if (canSend && clientRef.current) {
        try {
          clientRef.current.send(message);
          return true;
        } catch {
          /* fall through to queue */
        }
      }

      const queued = mapOutboundMessage(message);
      if (queued) {
        addToQueue(queued);
      }
      return false;
    },
    [canSend, clientRef, addToQueue],
  );

  return { send };
}

export function queueTypeForMessage(message: OutboundMessage): QueuedActionType | null {
  return mapOutboundMessage(message)?.type ?? null;
}
