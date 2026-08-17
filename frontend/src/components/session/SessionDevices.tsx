import type { SessionDevice } from "../../types";
import styles from "./SessionDevices.module.css";

interface SessionDevicesProps {
  devices: SessionDevice[];
  visible: boolean;
}

export function SessionDevices({ devices, visible }: SessionDevicesProps) {
  if (!visible) return null;

  return (
    <div className={styles.panel} aria-label="Dispositivi sessione">
      <div className={styles.title}>Session shared</div>
      <div className={styles.row}>
        {devices.map((d) => (
          <span
            key={d.id}
            className={`${styles.device} ${d.online ? styles.online : styles.offline}`}
          >
            {d.label} {d.online ? "online" : "offline"}
          </span>
        ))}
      </div>
    </div>
  );
}
