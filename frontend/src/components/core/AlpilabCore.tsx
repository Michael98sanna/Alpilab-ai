import type { CoreState } from "../../types";
import styles from "./AlpilabCore.module.css";

const STATE_CLASS: Record<CoreState, string> = {
  IDLE: styles.idle,
  LISTENING: styles.listening,
  THINKING: styles.thinking,
  SPEAKING: styles.speaking,
  WORKING: styles.working,
  WARNING: styles.warning,
  ERROR: styles.error,
};

interface AlpilabCoreProps {
  state: CoreState;
}

export function AlpilabCore({ state }: AlpilabCoreProps) {
  return (
    <div className={styles.coreWrapper} aria-live="polite">
      <span className={styles.coreLabel}>Alpilab</span>
      <div
        className={`${styles.core} ${STATE_CLASS[state]}`}
        role="img"
        aria-label={`Assistente: ${state}`}
      >
        <div className={styles.ring} />
        <div className={styles.inner} />
      </div>
      <span className={styles.stateText}>{state}</span>
    </div>
  );
}
