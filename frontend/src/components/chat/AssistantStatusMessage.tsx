import type { CoreState } from "../../types";
import styles from "./AssistantStatusMessage.module.css";

const STATE_CLASS: Record<CoreState, string> = {
  IDLE: styles.idle,
  LISTENING: styles.listening,
  THINKING: styles.thinking,
  SPEAKING: styles.speaking,
  WORKING: styles.working,
  WARNING: styles.warning,
  ERROR: styles.error,
};

interface AssistantStatusMessageProps {
  state: CoreState;
  label: string;
  timestamp?: string;
}

/** Compact assistant status rendered inside the chat timeline (not sticky). */
export function AssistantStatusMessage({
  state,
  label,
  timestamp,
}: AssistantStatusMessageProps) {
  const prominence =
    state === "WARNING" || state === "ERROR"
      ? styles.prominent
      : state === "IDLE"
        ? styles.subtle
        : styles.normal;

  return (
    <div
      className={`${styles.wrapper} ${prominence} ${STATE_CLASS[state]}`}
      role="status"
      aria-label={`Alpilab: ${state}`}
      data-testid="assistant-status"
    >
      <div className={styles.row}>
        <div className={styles.coreMini} aria-hidden="true">
          <div className={styles.ring} />
          <div className={styles.inner} />
        </div>
        <div className={styles.text}>
          <span className={styles.title}>ALPILAB AI</span>
          <span className={styles.label}>{label}</span>
          <span className={styles.stateTag}>{state}</span>
        </div>
      </div>
      {timestamp && <span className={styles.time}>{timestamp}</span>}
    </div>
  );
}
