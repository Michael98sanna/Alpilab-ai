import { useState } from "react";
import type { DiagnosticTest } from "../../types";
import { Button } from "../ui/Button";
import styles from "./DiagnosticPanel.module.css";

interface DiagnosticPanelProps {
  tests: DiagnosticTest[];
  nextTest?: DiagnosticTest;
  expanded: boolean;
  onToggle: () => void;
  onSubmitMeasurement: (testId: string, value: string) => void;
  onPause: () => void;
  onResume: () => void;
  isPaused: boolean;
  variant?: "inline" | "sheet";
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

function shortName(name: string) {
  if (name === "Battery voltage") return "Battery";
  if (name === "USB communication") return "USB";
  return name;
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
  expanded,
  onToggle,
  onSubmitMeasurement,
  onPause,
  onResume,
  isPaused,
  variant = "inline",
}: DiagnosticPanelProps) {
  const [value, setValue] = useState("");

  if (tests.length === 0) return null;

  function handleSubmit() {
    if (!nextTest || !value.trim()) return;
    onSubmitMeasurement(nextTest.id, value.trim());
    setValue("");
  }

  const panelClass =
    variant === "sheet" ? `${styles.panel} ${styles.sheet}` : styles.panel;

  if (!expanded) {
    return (
      <section className={styles.collapsed} aria-label="Diagnostica" data-testid="diagnostics-collapsed">
        <div className={styles.collapsedHeader}>DIAGNOSI</div>
        <div className={styles.collapsedList}>
          {tests.map((t) => (
            <span key={t.id} className={styles.collapsedItem}>
              {statusIcon(t.status)} {shortName(t.name)}
              {t.value ? ` ${t.value}` : ""}
            </span>
          ))}
        </div>
        <Button size="small" variant="ghost" onClick={onToggle}>
          Apri diagnosi
        </Button>
      </section>
    );
  }

  return (
    <section className={panelClass} aria-label="Diagnostica" data-testid="diagnostics-expanded">
      <div className={styles.panelHeader}>
        <span>Diagnostica</span>
        <button type="button" className={styles.collapseBtn} onClick={onToggle}>
          Chiudi
        </button>
      </div>

      <div className={styles.list}>
        {tests.map((t) => (
          <div key={t.id} className={styles.testRow}>
            <span>{t.name}</span>
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
