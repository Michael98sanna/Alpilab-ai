import type { RepairSession } from "../../types";
import styles from "./RepairBanner.module.css";

interface RepairBannerProps {
  session: RepairSession;
}

export function RepairBanner({ session }: RepairBannerProps) {
  if (session.status === "none") {
    return (
      <div className={styles.panel}>
        <p className={styles.empty}>Nessuna riparazione attiva</p>
      </div>
    );
  }

  return (
    <div className={styles.panel} aria-label="Riparazione attiva">
      <div className={styles.title}>Session active — {session.label}</div>
      <div className={styles.row}>
        <span className={styles.label}>Device</span>
        <span className={styles.value}>{session.device ?? "—"}</span>
      </div>
      <div className={styles.row}>
        <span className={styles.label}>Issue</span>
        <span className={styles.value}>{session.issue ?? "—"}</span>
      </div>
      <div className={styles.row}>
        <span className={styles.label}>Status</span>
        <span
          className={`${styles.value} ${
            session.status === "paused" ? styles.statusPaused : styles.statusActive
          }`}
        >
          {session.diagnosisLabel}
        </span>
      </div>
    </div>
  );
}
