import styles from "./MobileContextBar.module.css";

interface MobileContextBarProps {
  onOpenDiagnostics: () => void;
  onOpenTools: () => void;
  diagnosticsActive?: boolean;
  toolsActive?: boolean;
}

export function MobileContextBar({
  onOpenDiagnostics,
  onOpenTools,
  diagnosticsActive = false,
  toolsActive = false,
}: MobileContextBarProps) {
  return (
    <div className={styles.bar} data-testid="context-access-bar">
      <button
        type="button"
        className={`${styles.btn} ${diagnosticsActive ? styles.active : ""}`}
        onClick={onOpenDiagnostics}
        aria-label="Apri diagnosi"
      >
        Diagnosi
      </button>
      <span className={styles.dot} aria-hidden="true">
        ·
      </span>
      <button
        type="button"
        className={`${styles.btn} ${toolsActive ? styles.active : ""}`}
        onClick={onOpenTools}
        aria-label="Apri strumenti"
      >
        Strumenti
      </button>
    </div>
  );
}
