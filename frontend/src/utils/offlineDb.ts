import type { QueuedAction } from "../hooks/useOfflineQueue";

const DB_NAME = "alpilab-offline";
const DB_VERSION = 1;
const QUEUE_STORE = "queue";
const RESPONSE_STORE = "responses";

interface CachedResponse {
  key: string;
  data: unknown;
  timestamp: number;
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error ?? new Error("IndexedDB open failed"));
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(QUEUE_STORE)) {
        db.createObjectStore(QUEUE_STORE, { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains(RESPONSE_STORE)) {
        db.createObjectStore(RESPONSE_STORE, { keyPath: "key" });
      }
    };
  });
}

function runTransaction<T>(
  storeName: string,
  mode: IDBTransactionMode,
  operation: (store: IDBObjectStore) => IDBRequest<T> | void,
): Promise<T | void> {
  return openDb().then(
    (db) =>
      new Promise<T | void>((resolve, reject) => {
        const tx = db.transaction(storeName, mode);
        const store = tx.objectStore(storeName);
        const request = operation(store);

        tx.oncomplete = () => {
          db.close();
          if (request instanceof IDBRequest) {
            resolve(request.result);
          } else {
            resolve();
          }
        };
        tx.onerror = () => {
          db.close();
          reject(tx.error ?? new Error("IndexedDB transaction failed"));
        };
      }),
  );
}

export async function loadQueueFromDb(): Promise<QueuedAction[]> {
  if (typeof indexedDB === "undefined") {
    return [];
  }

  const items = await runTransaction<QueuedAction[]>(QUEUE_STORE, "readonly", (store) =>
    store.getAll(),
  );
  return Array.isArray(items) ? items : [];
}

export async function persistQueueItem(item: QueuedAction): Promise<void> {
  if (typeof indexedDB === "undefined") {
    return;
  }
  await runTransaction(QUEUE_STORE, "readwrite", (store) => store.put(item));
}

export async function removeQueueItem(id: string): Promise<void> {
  if (typeof indexedDB === "undefined") {
    return;
  }
  await runTransaction(QUEUE_STORE, "readwrite", (store) => store.delete(id));
}

export async function cacheResponse(key: string, data: unknown): Promise<void> {
  if (typeof indexedDB === "undefined") {
    return;
  }

  const entry: CachedResponse = {
    key,
    data,
    timestamp: Date.now(),
  };
  await runTransaction(RESPONSE_STORE, "readwrite", (store) => store.put(entry));
}

export async function getCachedResponse(key: string): Promise<unknown | null> {
  if (typeof indexedDB === "undefined") {
    return null;
  }

  const entry = await runTransaction<CachedResponse>(RESPONSE_STORE, "readonly", (store) =>
    store.get(key),
  );
  return entry?.data ?? null;
}

export async function clearSyncedQueueItems(items: QueuedAction[]): Promise<void> {
  if (typeof indexedDB === "undefined") {
    return;
  }

  await runTransaction(QUEUE_STORE, "readwrite", (store) => {
    for (const item of items) {
      if (item.status === "synced") {
        store.delete(item.id);
      } else {
        store.put(item);
      }
    }
  });
}
