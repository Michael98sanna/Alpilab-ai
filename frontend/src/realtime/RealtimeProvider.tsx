import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  type ReactNode,
} from "react";
import { getAppMode, getSessionIdFromUrl, type AppMode } from "../config/env";
import { useRepairSession, type RepairSessionApi } from "../hooks/useRepairSession";
import type { RepairAction } from "../types";
import { RealtimeClient } from "./RealtimeClient";
import { mapWsMessageToActions } from "./mapEvents";
import {
  loadDeviceName,
  loadDeviceType,
  loadOrCreateDeviceId,
  loadSessionId,
} from "./sessionStorage";

interface SessionContextValue extends RepairSessionApi {
  mode: AppMode;
  sessionId: string;
  deviceId: string;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const mode = getAppMode();
  const isRealtime = mode === "realtime";
  const sessionId = loadSessionId(getSessionIdFromUrl());
  const deviceId = loadOrCreateDeviceId();
  const deviceType = loadDeviceType();
  const deviceName = loadDeviceName(deviceType);

  const session = useRepairSession(!isRealtime);
  const clientRef = useRef<RealtimeClient | null>(null);
  const dispatchRef = useRef(session.dispatch);

  dispatchRef.current = session.dispatch;

  useEffect(() => {
    if (!isRealtime) return;

    const client = new RealtimeClient({
      sessionId,
      deviceId,
      deviceType,
      deviceName,
      seedDemo: Boolean(getSessionIdFromUrl()) || true,
      onMessage: (msg) => {
        const actions = mapWsMessageToActions(msg);
        actions.forEach((action) => dispatchRef.current(action));
      },
      onConnectionChange: (connectionState) => {
        dispatchRef.current({ type: "SET_CONNECTION_STATE", state: connectionState });
      },
    });

    clientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
      clientRef.current = null;
    };
  }, [isRealtime, sessionId, deviceId, deviceType, deviceName]);

  const sendMessageRealtime = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || !clientRef.current) return;
    clientRef.current.send({ type: "chat_message", content: trimmed, role: "user" });
  }, []);

  const value: SessionContextValue = useMemo(
    () => ({
      ...session,
      mode,
      sessionId,
      deviceId,
      sendMessage: isRealtime ? sendMessageRealtime : session.sendMessage,
    }),
    [session, mode, sessionId, deviceId, isRealtime, sendMessageRealtime],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useAppSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useAppSession must be used within RealtimeProvider");
  }
  return ctx;
}

export type { RepairAction };
