import { useState } from "react";
import type { DiagnosticTest } from "../../types";
import { Button } from "../ui/Button";
import styles from "./DiagnosticPanel.module.css";

interface DiagnosticPanelProps {
  tests: DiagnosticTest[];
  nextTest?: DiagnosticTest;
  onClose: () => void;
  onSubmitMeasurement: (testId: string, value: string) => void;
  onPause: () => void;
  onResume: () => void;
  isPaused: boolean;
  variant?: "sheet" | "side";
  showHeader?: boolean;
}

function statusIcon(status: DiagnosticTest["status"]) {
  switch (status) {
    case "PASSED":
      return "✓";
    case "FAILED":
      return "✕";
    default:
      return "○";
  }
}

function statusClass(status: DiagnosticTest["status"]) {
  switch (status) {
    case "PASSED":
      return styles.statusPassed;
    case "FAILED":
      return styles.statusFailed;
    default:
      return styles.statusPending;
  }
}

export function DiagnosticPanel({
  tests,
  nextTest,
  onClose,
  onSubmitMeasurement,
  onPause,
  onResume,
  isPaused,
  variant = "sheet",
  showHeader = false,
}: DiagnosticPanelProps) {
  const [value, setValue] = useState("");

  if (tests.length === 0) return null;

  function handleSubmit() {
    if (!nextTest || !value.trim()) return;
    onSubmitMeasurement(nextTest.id, value.trim());
    setValue("");
  }

  const panelClass =
    variant === "side"
      ? `${styles.panel} ${styles.side}`
      : `${styles.panel} ${styles.content}`;

  return (
    <section
      className={panelClass}
      aria-label="Diagnostica"
      data-testid="diagnostics-expanded"
    >
      {showHeader && (
        <div className={styles.panelHeader}>
          <span>Diagnostica</span>
          <button type="button" className={styles.collapseBtn} onClick={onClose}>
            Chiudi
          </button>
        </div>
      )}

      <div className={styles.list}>
        {tests.map((t) => (
          <div key={t.id} className={styles.testRow}>
            <span>
              {statusIcon(t.status)} {t.name}
            </span>
            <span className={statusClass(t.status)}>
              {t.value ?? t.status}
            </span>
          </div>
        ))}
      </div>

      {nextTest && (
        <div>
          <div className={styles.title}>Next test</div>
          <div className={styles.testName}>Misura {nextTest.name}</div>
          <div className={styles.form}>
            <input
              className={styles.input}
              type="text"
              placeholder="0.00 V"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              aria-label="Valore misura"
            />
            <Button variant="primary" onClick={handleSubmit}>
              Inserisci
            </Button>
          </div>
        </div>
      )}

      <div className={styles.actions}>
        {isPaused ? (
          <Button size="small" onClick={onResume}>
            Continua diagnosi
          </Button>
        ) : (
          <Button size="small" variant="ghost" onClick={onPause}>
            Pausa diagnosi
          </Button>
        )}
      </div>
    </section>
  );
}
