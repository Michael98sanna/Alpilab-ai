import { useOfflineQueue } from "../hooks/useOfflineQueue";
import styles from "./OfflineIndicator.module.css";

export function OfflineIndicator() {
  const { isOnline, queue } = useOfflineQueue();
  const pendingCount = queue.filter((action) => action.status === "pending").length;
  const syncingCount = queue.filter((action) => action.status === "syncing").length;

  if (isOnline && pendingCount === 0 && syncingCount === 0) {
    return null;
  }

  let variant: "offline" | "syncing" | "synced" = "offline";
  let label = "Offline — Sincronizzazione locale";

  if (isOnline && (pendingCount > 0 || syncingCount > 0)) {
    variant = "syncing";
    label = `Sincronizzazione ${pendingCount + syncingCount} azioni...`;
  } else if (isOnline && pendingCount === 0) {
    variant = "synced";
    label = "Sincronizzato";
  }

  return (
    <div
      className={styles.offlineIndicator}
      data-variant={variant}
      role="status"
      aria-live="polite"
      data-testid="offline-indicator"
    >
      {label}
    </div>
  );
}
