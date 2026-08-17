import type { RepairSession } from "../../types";
import styles from "./RepairContextBanner.module.css";

interface RepairContextBannerProps {
  session: RepairSession;
}

export function RepairContextBanner({ session }: RepairContextBannerProps) {
  if (session.status === "none" || !session.device) {
    return null;
  }

  const isPaused = session.status === "paused";

  return (
    <div className={styles.banner} aria-label="Contesto riparazione" data-testid="repair-context">
      <div className={styles.main}>
        <span className={styles.device}>{session.device}</span>
        <span className={styles.sep}>·</span>
        <span className={styles.issue}>{session.issue}</span>
      </div>
      <span className={`${styles.status} ${isPaused ? styles.paused : styles.active}`}>
        ● {session.diagnosisLabel}
      </span>
    </div>
  );
}
