import type { CoreState } from "../../types";
import { STATUS_LABELS } from "../../types";
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

/** Compact sticky Alpilab status above chat input — not in timeline. */
export function AlpilabStatusBar({ state }: AlpilabStatusBarProps) {
  const label = STATUS_LABELS[state];
  const isAlert = state === "WARNING" || state === "ERROR";

  return (
    <div
      className={`${styles.bar} ${STATE_CLASS[state]}`}
      role="status"
      aria-live="polite"
      aria-label={`Alpilab: ${label}`}
      data-testid="alpilab-status-bar"
    >
      {isAlert ? (
        <span className={state === "ERROR" ? styles.errorIcon : styles.warningIcon} aria-hidden="true">
          ⚠
        </span>
      ) : (
        <div className={styles.coreMini} aria-hidden="true">
          <div className={styles.ring} />
          <div className={styles.inner} />
        </div>
      )}
      <div className={styles.text}>
        <span className={styles.brand}>ALPILAB AI</span>
        <span className={styles.sep}>·</span>
        <span className={styles.label}>{label}</span>
      </div>
    </div>
  );
}
