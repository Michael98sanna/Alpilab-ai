import type { SessionDevice } from "../../types";
import styles from "./SessionDevicesCompact.module.css";

interface SessionDevicesCompactProps {
  devices: SessionDevice[];
  expanded: boolean;
  onToggle: () => void;
}

export function SessionDevicesCompact({
  devices,
  expanded,
  onToggle,
}: SessionDevicesCompactProps) {
  const onlineCount = devices.filter((d) => d.online).length;

  return (
    <div className={styles.wrap}>
      <button
        type="button"
        className={styles.chip}
        onClick={onToggle}
        aria-expanded={expanded}
        aria-label={`${onlineCount} di ${devices.length} dispositivi online`}
        data-testid="session-devices-chip"
      >
        <span className={styles.dot} aria-hidden="true" />
        {devices.length} dispositivi
      </button>

      {expanded && (
        <div className={styles.dropdown} role="dialog" aria-label="Session shared">
          {devices.map((d) => (
            <div key={d.id} className={styles.row}>
              <span>{d.label}</span>
              <span className={d.online ? styles.online : styles.offline}>
                {d.online ? "● online" : "○ offline"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
