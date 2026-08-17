import type { SessionDevice } from "../../types";
import { SessionDevicesCompact } from "./SessionDevicesCompact";
import styles from "./AppHeader.module.css";

interface AppHeaderProps {
  devices?: SessionDevice[];
  sessionDevicesExpanded?: boolean;
  onToggleSessionDevices?: () => void;
  onVoiceClick?: () => void;
}

export function AppHeader({
  devices = [],
  sessionDevicesExpanded = false,
  onToggleSessionDevices,
  onVoiceClick,
}: AppHeaderProps) {
  return (
    <header className={styles.header} role="banner">
      <div className={styles.brand}>ALPILAB AI</div>
      <div className={styles.right}>
        {devices.length > 0 && onToggleSessionDevices && (
          <SessionDevicesCompact
            devices={devices}
            expanded={sessionDevicesExpanded}
            onToggle={onToggleSessionDevices}
          />
        )}
        <button
          type="button"
          className={styles.micBtn}
          aria-label="Attiva microfono"
          onClick={onVoiceClick}
        >
          🎙️
        </button>
        <div className={styles.user}>
          <span className={styles.dot} aria-hidden="true" />
          <span>Michael</span>
        </div>
      </div>
    </header>
  );
}
