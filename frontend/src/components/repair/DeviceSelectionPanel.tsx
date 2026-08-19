import type { DetectedDevice, DeviceContext } from "../../types";
import styles from "./DeviceSelectionPanel.module.css";

interface DeviceSelectionPanelProps {
  detectedDevices: DetectedDevice[];
  deviceContext: DeviceContext | null;
  onAssociate: (deviceId: string) => void;
  onUnassociate: () => void;
  onDismiss: () => void;
}

function deviceDisplayName(d: DetectedDevice): string {
  if (d.brand && d.model) return `${d.brand} ${d.model}`;
  if (d.model) return d.model;
  if (d.brand) return d.brand;
  return d.serial_number ?? d.id;
}

function contextDisplayName(ctx: DeviceContext): string {
  if (ctx.brand && ctx.model) return `${ctx.brand} ${ctx.model}`;
  if (ctx.model) return ctx.model;
  if (ctx.brand) return ctx.brand;
  return "Dispositivo associato";
}

export function DeviceSelectionPanel({
  detectedDevices,
  deviceContext,
  onAssociate,
  onUnassociate,
  onDismiss,
}: DeviceSelectionPanelProps) {
  const hasDetected = detectedDevices.length > 0;
  const hasContext = deviceContext !== null;

  // Nothing to show
  if (!hasDetected && !hasContext) return null;

  return (
    <div className={styles.panel} role="region" aria-label="Dispositivo riparazione" data-testid="device-selection-panel">
      {/* Device context: already associated */}
      {hasContext && (
        <div className={styles.associated} data-testid="device-context">
          <span className={styles.labelSmall}>Dispositivo della riparazione</span>
          <span className={styles.deviceName}>{contextDisplayName(deviceContext!)}</span>
          {deviceContext!.serial_number && (
            <span className={styles.serial}>{deviceContext!.serial_number}</span>
          )}
          <button
            type="button"
            className={styles.removeBtn}
            onClick={onUnassociate}
            data-testid="unassociate-btn"
          >
            Rimuovi
          </button>
        </div>
      )}

      {/* Detected devices list */}
      {hasDetected && (
        <div className={styles.detectedSection} data-testid="detected-devices-section">
          <span className={styles.labelSmall}>
            {detectedDevices.length === 1
              ? "Dispositivo rilevato"
              : "Dispositivi rilevati"}
          </span>
          <ul className={styles.deviceList}>
            {detectedDevices.map((d) => {
              const isAssociated = hasContext && deviceContext!.id === d.id;
              return (
                <li key={d.id} className={styles.deviceItem} data-testid={`detected-device-${d.id}`}>
                  <div className={styles.deviceInfo}>
                    <span className={styles.deviceName}>{deviceDisplayName(d)}</span>
                    {d.variant && <span className={styles.serial}>{d.variant}</span>}
                    {!d.variant && d.serial_number && (
                      <span className={styles.serial}>{d.serial_number}</span>
                    )}
                    {d.metadata?.adb_state && d.metadata.adb_state !== "device" && (
                      <span className={styles.stateTag} data-testid="adb-state">
                        {String(d.metadata.adb_state)}
                      </span>
                    )}
                  </div>
                  {!isAssociated && (
                    <button
                      type="button"
                      className={styles.associateBtn}
                      onClick={() => onAssociate(d.id)}
                      data-testid={`associate-btn-${d.id}`}
                    >
                      Associa
                    </button>
                  )}
                  {isAssociated && (
                    <span className={styles.associatedBadge} data-testid="associated-badge">
                      ✓ Associato
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
          {!hasContext && (
            <button
              type="button"
              className={styles.dismissBtn}
              onClick={onDismiss}
              data-testid="dismiss-btn"
            >
              Ignora
            </button>
          )}
        </div>
      )}
    </div>
  );
}
