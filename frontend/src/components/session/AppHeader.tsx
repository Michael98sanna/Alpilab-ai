import type { SessionDevice } from "../../types";
import { SessionDevicesCompact } from "./SessionDevicesCompact";
import styles from "./AppHeader.module.css";

interface AppHeaderProps {
  devices?: SessionDevice[];
  sessionDevicesExpanded?: boolean;
  onToggleSessionDevices?: () => void;
  onVoiceClick?: () => void;
  onPairDevice?: () => void;
  connectionState?: import("../../types").ConnectionState;
  showConnection?: boolean;
  pcAgent?: import("../../types").PcAgentStatus | null;
}

export function AppHeader({
  devices = [],
  sessionDevicesExpanded = false,
  onToggleSessionDevices,
  onVoiceClick,
  onPairDevice,
  connectionState = "DISCONNECTED",
  showConnection = false,
  pcAgent = null,
}: AppHeaderProps) {
  const connectionLabel =
    connectionState === "CONNECTED"
      ? "Connected"
      : connectionState === "UNAUTHORIZED"
        ? "Dispositivo non autorizzato"
      : connectionState === "RECONNECTING"
        ? "Reconnecting…"
        : connectionState === "CONNECTING"
          ? "Connecting…"
          : connectionState === "ERROR"
            ? "Offline"
            : "Offline";

  return (
    <header className={styles.header} role="banner">
      <div className={styles.brand}>ALPILAB AI</div>
      <div className={styles.right}>
        {showConnection && (
          <span
            className={styles.connection}
            data-testid="connection-status"
            aria-label={`Connection: ${connectionLabel}`}
          >
            {connectionState === "CONNECTED" ? "●" : "○"} {connectionLabel}
          </span>
        )}
        {pcAgent && (
          <span
            className={styles.connection}
            data-testid="pc-agent-status"
            aria-label={`PC Agent: ${pcAgent.online ? "online" : "offline"}`}
          >
            {pcAgent.online ? "●" : "○"} PC Agent
          </span>
        )}
        {devices.length > 0 && onToggleSessionDevices && (
          <SessionDevicesCompact
            devices={devices}
            expanded={sessionDevicesExpanded}
            onToggle={onToggleSessionDevices}
          />
        )}
        {onPairDevice && (
          <button
            type="button"
            className={styles.pairBtn}
            onClick={onPairDevice}
            data-testid="pair-device"
          >
            Collega dispositivo
          </button>
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
