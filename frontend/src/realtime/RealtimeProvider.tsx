import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { getAppMode, type AppMode } from "../config/env";
import { useRepairSession, type RepairSessionApi } from "../hooks/useRepairSession";
import type { RepairAction } from "../types";
import { RealtimeClient } from "./RealtimeClient";
import { mapWsMessageToActions, shouldRequestSnapshot } from "./mapEvents";
import {
  isPcLoopbackUi,
  loadDeviceName,
  loadDeviceType,
  loadOrCreateDeviceId,
  loadPairingToken,
  loadSessionId,
  resolveSessionIdFromHub,
} from "./sessionStorage";

interface SessionContextValue extends RepairSessionApi {
  mode: AppMode;
  sessionId: string;
  deviceId: string;
  associateDevice: (deviceId: string) => void;
  unassociateDevice: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const mode = getAppMode();
  const isRealtime = mode === "realtime";
  const [sessionId, setSessionId] = useState(loadSessionId);
  const deviceId = loadOrCreateDeviceId();
  const deviceType = loadDeviceType();
  const deviceName = loadDeviceName(deviceType);
  const pairingToken = loadPairingToken();
  const pcLoopback = isPcLoopbackUi();

  const session = useRepairSession(!isRealtime);
  const clientRef = useRef<RealtimeClient | null>(null);
  const dispatchRef = useRef(session.dispatch);
  const stateVersionRef = useRef(session.state.stateVersion);
  const wasReconnectingRef = useRef(false);

  dispatchRef.current = session.dispatch;
  stateVersionRef.current = session.state.stateVersion;

  useEffect(() => {
    let cancelled = false;
    void resolveSessionIdFromHub().then((id) => {
      if (!cancelled && id !== sessionId) {
        setSessionId(id);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    if (!isRealtime) return;

    const client = new RealtimeClient({
      sessionId,
      deviceId,
      deviceType,
      deviceName,
      pairingToken: pcLoopback ? null : pairingToken,
      seedDemo: pcLoopback && deviceType === "pc",
      onMessage: (msg) => {
        if (msg.type === "event" && msg.event?.event_type === "SESSION_STATE_UPDATED") {
          const incoming = Number(msg.event.payload.state_version);
          if (shouldRequestSnapshot(stateVersionRef.current, incoming)) {
            clientRef.current?.send({ type: "request_snapshot" });
            return;
          }
        }
        const actions = mapWsMessageToActions(msg);
        actions.forEach((action) => dispatchRef.current(action));
      },
      onConnectionChange: (connectionState) => {
        dispatchRef.current({ type: "SET_CONNECTION_STATE", state: connectionState });
        if (connectionState === "RECONNECTING") {
          wasReconnectingRef.current = true;
        }
        if (connectionState === "CONNECTED" && wasReconnectingRef.current) {
          wasReconnectingRef.current = false;
          clientRef.current?.send({ type: "request_snapshot" });
        }
      },
    });

    clientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
      clientRef.current = null;
    };
  }, [isRealtime, sessionId, deviceId, deviceType, deviceName, pairingToken, pcLoopback]);

  const sendMessageRealtime = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || !clientRef.current) return;
    clientRef.current.send({ type: "chat_message", content: trimmed, role: "user" });
  }, []);

  const submitMeasurementRealtime = useCallback((testId: string, value: string) => {
    if (!clientRef.current || !value.trim()) return;
    dispatchRef.current({ type: "SET_SAVING_TEST", testId });
    clientRef.current.send({
      type: "diagnostic_update",
      test_id: testId,
      value: value.trim(),
    });
  }, []);

  const pauseDiagnosisRealtime = useCallback(() => {
    clientRef.current?.send({ type: "diagnosis_pause", paused: true });
  }, []);

  const resumeDiagnosisRealtime = useCallback(() => {
    clientRef.current?.send({ type: "diagnosis_pause", paused: false });
  }, []);

  const associateDevice = useCallback((deviceId: string) => {
    clientRef.current?.send({ type: "associate_repair_device", repair_device_id: deviceId });
    // Optimistic local dispatch not needed — server will emit REPAIR_DEVICE_ASSOCIATED
  }, []);

  const unassociateDevice = useCallback(() => {
    clientRef.current?.send({ type: "unassociate_repair_device" });
  }, []);

  const value: SessionContextValue = useMemo(
    () => ({
      ...session,
      mode,
      sessionId,
      deviceId,
      sendMessage: isRealtime ? sendMessageRealtime : session.sendMessage,
      submitMeasurement: isRealtime
        ? submitMeasurementRealtime
        : session.submitMeasurement,
      pauseDiagnosis: isRealtime ? pauseDiagnosisRealtime : session.pauseDiagnosis,
      resumeDiagnosis: isRealtime ? resumeDiagnosisRealtime : session.resumeDiagnosis,
      associateDevice,
      unassociateDevice,
    }),
    [
      session,
      mode,
      sessionId,
      deviceId,
      isRealtime,
      sendMessageRealtime,
      submitMeasurementRealtime,
      pauseDiagnosisRealtime,
      resumeDiagnosisRealtime,
      associateDevice,
      unassociateDevice,
    ],
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
