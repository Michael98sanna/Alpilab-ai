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
import {
  clearSyncedQueueItems,
  loadQueueFromDb,
  persistQueueItem,
} from "../utils/offlineDb";

export type QueuedActionType =
  | "CHAT_MESSAGE"
  | "DIAGNOSTIC_UPDATE"
  | "TOOL_EXECUTE"
  | "REALTIME_MESSAGE";

export interface QueuedAction {
  id: string;
  type: QueuedActionType;
  payload: Record<string, unknown>;
  timestamp: number;
  status: "pending" | "syncing" | "synced" | "failed";
}

interface OfflineQueueContextValue {
  queue: QueuedAction[];
  isOnline: boolean;
  addToQueue: (action: Omit<QueuedAction, "id" | "timestamp" | "status">) => string;
  syncQueue: (send: (action: QueuedAction) => Promise<void>) => Promise<void>;
  registerSyncHandler: (send: ((action: QueuedAction) => Promise<void>) | null) => void;
}

const OfflineQueueContext = createContext<OfflineQueueContextValue | null>(null);

export function OfflineQueueProvider({ children }: { children: ReactNode }) {
  const [queue, setQueue] = useState<QueuedAction[]>([]);
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true,
  );
  const queueRef = useRef<QueuedAction[]>([]);
  const syncHandlerRef = useRef<((action: QueuedAction) => Promise<void>) | null>(null);
  const syncingRef = useRef(false);

  queueRef.current = queue;

  useEffect(() => {
    void loadQueueFromDb().then((items) => {
      if (items.length > 0) {
        setQueue(items);
      }
    });
  }, []);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const addToQueue = useCallback(
    (action: Omit<QueuedAction, "id" | "timestamp" | "status">) => {
      const newAction: QueuedAction = {
        ...action,
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        timestamp: Date.now(),
        status: "pending",
      };

      setQueue((prev) => {
        const next = [...prev, newAction];
        queueRef.current = next;
        return next;
      });
      void persistQueueItem(newAction);
      return newAction.id;
    },
    [],
  );

  const syncQueue = useCallback(async (send: (action: QueuedAction) => Promise<void>) => {
    if (syncingRef.current) {
      return;
    }

    syncingRef.current = true;
    const pendingActions = queueRef.current.filter((action) => action.status === "pending");
    let workingQueue = [...queueRef.current];

    for (const action of pendingActions) {
      workingQueue = workingQueue.map((item) =>
        item.id === action.id ? { ...item, status: "syncing" } : item,
      );
      setQueue(workingQueue);
      queueRef.current = workingQueue;
      await persistQueueItem({ ...action, status: "syncing" });

      try {
        await send(action);
        workingQueue = workingQueue.map((item) =>
          item.id === action.id ? { ...item, status: "synced" } : item,
        );
      } catch {
        workingQueue = workingQueue.map((item) =>
          item.id === action.id ? { ...item, status: "failed" } : item,
        );
      }

      setQueue(workingQueue);
      queueRef.current = workingQueue;
      await clearSyncedQueueItems(workingQueue);
    }

    syncingRef.current = false;
  }, []);

  const registerSyncHandler = useCallback(
    (send: ((action: QueuedAction) => Promise<void>) | null) => {
      syncHandlerRef.current = send;
    },
    [],
  );

  useEffect(() => {
    if (!isOnline || !syncHandlerRef.current) {
      return;
    }

    const timer = window.setTimeout(() => {
      if (syncHandlerRef.current) {
        void syncQueue(syncHandlerRef.current);
      }
    }, 1000);

    return () => window.clearTimeout(timer);
  }, [isOnline, queue.length, syncQueue]);

  const value = useMemo(
    () => ({
      queue,
      isOnline,
      addToQueue,
      syncQueue,
      registerSyncHandler,
    }),
    [queue, isOnline, addToQueue, syncQueue, registerSyncHandler],
  );

  return (
    <OfflineQueueContext.Provider value={value}>{children}</OfflineQueueContext.Provider>
  );
}

export function useOfflineQueue(): OfflineQueueContextValue {
  const context = useContext(OfflineQueueContext);
  if (!context) {
    throw new Error("useOfflineQueue must be used within OfflineQueueProvider");
  }
  return context;
}
