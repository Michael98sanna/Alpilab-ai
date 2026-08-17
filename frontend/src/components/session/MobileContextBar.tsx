import styles from "./MobileContextBar.module.css";

interface MobileContextBarProps {
  onOpenDiagnostics: () => void;
  onOpenTools: () => void;
  diagnosticsActive?: boolean;
}

export function MobileContextBar({
  onOpenDiagnostics,
  onOpenTools,
  diagnosticsActive = false,
}: MobileContextBarProps) {
  return (
    <div className={styles.bar} data-testid="mobile-context-bar">
      <button
        type="button"
        className={`${styles.btn} ${diagnosticsActive ? styles.active : ""}`}
        onClick={onOpenDiagnostics}
        aria-label="Apri diagnosi"
      >
        📋 Diagnosi
      </button>
      <button type="button" className={styles.btn} onClick={onOpenTools} aria-label="Apri strumenti">
        🛠 Strumenti
      </button>
    </div>
  );
}
