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
import { useOfflineQueue } from "../hooks/useOfflineQueue";
import { useRealtimeClient } from "../hooks/useRealtimeClient";
import { useRepairSession, type RepairSessionApi } from "../hooks/useRepairSession";
import type { RepairAction } from "../types";
import { RealtimeClient } from "./RealtimeClient";
import { mapWsMessageToActions, shouldRequestSnapshot } from "./mapEvents";
import type { OutboundMessage } from "./types";
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
  requestSnapshot: () => void;
  associateDevice: (deviceId: string) => void;
  unassociateDevice: () => void;
  activateRepairDevice: (params: {
    repair_device_id: string;
    device_name: string;
    brand?: string | null;
    model?: string | null;
  }) => void;
  associateManualDevice: (brand: string, model: string) => string;
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

  const session = useRepairSession(false);
  const { isOnline, addToQueue, syncQueue, registerSyncHandler } = useOfflineQueue();
  const clientRef = useRef<RealtimeClient | null>(null);
  const dispatchRef = useRef(session.dispatch);
  const stateVersionRef = useRef(session.state.stateVersion);
  const wasReconnectingRef = useRef(false);

  dispatchRef.current = session.dispatch;
  stateVersionRef.current = session.state.stateVersion;

  const canSendRealtime =
    isOnline && session.state.connectionState === "CONNECTED";

  const { send: sendRealtime } = useRealtimeClient({
    clientRef,
    canSend: canSendRealtime,
    addToQueue,
  });

  useEffect(() => {
    registerSyncHandler(async (action) => {
      if (!clientRef.current) {
        throw new Error("WebSocket not connected");
      }
      clientRef.current.send(action.payload as OutboundMessage);
    });
    return () => registerSyncHandler(null);
  }, [registerSyncHandler]);

  useEffect(() => {
    if (!isRealtime || !isOnline || session.state.connectionState !== "CONNECTED") {
      return;
    }
    void syncQueue(async (action) => {
      if (!clientRef.current) {
        throw new Error("WebSocket not connected");
      }
      clientRef.current.send(action.payload as OutboundMessage);
    });
  }, [isRealtime, isOnline, session.state.connectionState, syncQueue]);

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
      seedDemo: false,
      onMessage: (msg) => {
        if (msg.type === "event" && msg.event?.event_type === "SESSION_STATE_UPDATED") {
          const incoming = Number(msg.event.payload.state_version);
          if (shouldRequestSnapshot(stateVersionRef.current, incoming)) {
            clientRef.current?.send({ type: "request_snapshot" });
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
    if (!trimmed) return;
    sendRealtime({ type: "chat_message", content: trimmed, role: "user" });
  }, [sendRealtime]);

  const submitMeasurementRealtime = useCallback((testId: string, value: string) => {
    if (!value.trim()) return;
    dispatchRef.current({ type: "SET_SAVING_TEST", testId });
    sendRealtime({
      type: "diagnostic_update",
      test_id: testId,
      value: value.trim(),
    });
  }, [sendRealtime]);

  const pauseDiagnosisRealtime = useCallback(() => {
    sendRealtime({ type: "diagnosis_pause", paused: true });
  }, [sendRealtime]);

  const resumeDiagnosisRealtime = useCallback(() => {
    sendRealtime({ type: "diagnosis_pause", paused: false });
  }, [sendRealtime]);

  const requestSnapshot = useCallback(() => {
    sendRealtime({ type: "request_snapshot" });
  }, [sendRealtime]);

  const associateDevice = useCallback((deviceId: string) => {
    sendRealtime({ type: "associate_repair_device", repair_device_id: deviceId });
  }, [sendRealtime]);

  const activateRepairDevice = useCallback(
    (params: {
      repair_device_id: string;
      device_name: string;
      brand?: string | null;
      model?: string | null;
    }) => {
      sendRealtime({
        type: "activate_repair_device",
        repair_device_id: params.repair_device_id,
        device_name: params.device_name,
        brand: params.brand ?? undefined,
        model: params.model ?? undefined,
      });
    },
    [sendRealtime],
  );

  const associateManualDevice = useCallback(
    (brand: string, model: string) => {
      sendRealtime({ type: "associate_manual_repair_device", brand, model });
      return `manual-${Date.now().toString(36)}`;
    },
    [sendRealtime],
  );

  const unassociateDevice = useCallback(() => {
    sendRealtime({ type: "unassociate_repair_device" });
  }, [sendRealtime]);

  const value: SessionContextValue = useMemo(
    () => ({
      ...session,
      mode,
      sessionId,
      deviceId,
      requestSnapshot: isRealtime ? requestSnapshot : () => {},
      sendMessage: isRealtime ? sendMessageRealtime : session.sendMessage,
      submitMeasurement: isRealtime
        ? submitMeasurementRealtime
        : session.submitMeasurement,
      pauseDiagnosis: isRealtime ? pauseDiagnosisRealtime : session.pauseDiagnosis,
      resumeDiagnosis: isRealtime ? resumeDiagnosisRealtime : session.resumeDiagnosis,
      associateDevice,
      unassociateDevice,
      activateRepairDevice: isRealtime
        ? activateRepairDevice
        : session.activateRepairDevice,
      associateManualDevice: isRealtime
        ? associateManualDevice
        : session.associateManualDevice,
    }),
    [
      session,
      mode,
      sessionId,
      deviceId,
      isRealtime,
      requestSnapshot,
      sendMessageRealtime,
      submitMeasurementRealtime,
      pauseDiagnosisRealtime,
      resumeDiagnosisRealtime,
      associateDevice,
      unassociateDevice,
      activateRepairDevice,
      associateManualDevice,
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
