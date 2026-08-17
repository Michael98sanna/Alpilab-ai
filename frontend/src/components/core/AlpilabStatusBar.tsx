import type { CoreState } from "../../types";
import { getCoreStatusConfig } from "../../config/coreStatus";
import styles from "./AlpilabStatusBar.module.css";

const STATE_CLASS: Record<CoreState, string> = {
  IDLE: styles.idle,
  LISTENING: styles.listening,
  THINKING: styles.thinking,
  SPEAKING: styles.speaking,
  WORKING: styles.working,
  WARNING: styles.warning,
  ERROR: styles.error,
};

interface AlpilabStatusBarProps {
  state: CoreState;
}

/** Compact centered assistant status above chat input — driven by coreState. */
export function AlpilabStatusBar({ state }: AlpilabStatusBarProps) {
  const config = getCoreStatusConfig(state);
  const isAlert = config.variant === "warning" || config.variant === "error";

  const labelClass =
    config.variant === "warning"
      ? styles.labelWarning
      : config.variant === "error"
        ? styles.labelError
        : config.variant === "active"
          ? styles.labelActive
          : "";

  return (
    <div
      className={`${styles.bar} ${STATE_CLASS[state]}`}
      role="status"
      aria-live="polite"
      aria-label={config.ariaLabel}
      data-testid="alpilab-status-bar"
      data-core-state={state}
    >
      <div className={styles.center} data-testid="core-status-center">
        <div className={styles.indicatorRow} aria-hidden="true">
          {isAlert ? (
            <span className={styles.alertIcon}>⚠</span>
          ) : (
            <div className={styles.coreMini}>
              <div className={styles.ring} />
              <div className={styles.inner} />
            </div>
          )}
        </div>
        <span key={state} className={`${styles.label} ${labelClass}`} data-testid="core-status-label">
          {config.label}
        </span>
      </div>
    </div>
  );
}
