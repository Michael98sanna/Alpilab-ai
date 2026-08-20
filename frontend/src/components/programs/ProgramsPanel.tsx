import { useState } from "react";
import {
  LAB_PROGRAMS,
  canExecuteProgram,
  statusLabel,
  type LabProgram,
  type ProgramId,
} from "../../programs/catalog";
import { Button } from "../ui/Button";
import styles from "./ProgramsPanel.module.css";

export type ProgramActionResult = {
  ok: boolean;
  message: string;
};

interface ProgramsPanelProps {
  onOpenProgram: (program: LabProgram) => Promise<ProgramActionResult>;
  busyProgramId?: ProgramId | null;
}

export function ProgramsPanel({
  onOpenProgram,
  busyProgramId = null,
}: ProgramsPanelProps) {
  const [feedback, setFeedback] = useState<Record<string, string>>({});

  async function handleAction(program: LabProgram) {
    if (program.status === "future") {
      setFeedback((prev) => ({
        ...prev,
        [program.id]: "Integrazione futura — non disponibile.",
      }));
      return;
    }
    if (program.status === "configured" && !canExecuteProgram(program)) {
      setFeedback((prev) => ({
        ...prev,
        [program.id]: "Non ancora configurato",
      }));
      return;
    }

    const result = await onOpenProgram(program);
    setFeedback((prev) => ({ ...prev, [program.id]: result.message }));
  }

  return (
    <section
      className={styles.panel}
      aria-label="Programmi"
      data-testid="programs-panel"
    >
      <header className={styles.header}>
        <h2 className={styles.title}>Programmi</h2>
        <p className={styles.subtitle}>
          Software Windows del laboratorio. Solo i programmi operativi possono
          essere avviati.
        </p>
      </header>

      <ul className={styles.list}>
        {LAB_PROGRAMS.map((program) => {
          const busy = busyProgramId === program.id;
          const executable = canExecuteProgram(program);
          const checkChat =
            program.id === "alpilab_check" && program.status === "operational";
          const notConfigured =
            program.status === "configured" && !executable;
          const isFuture = program.status === "future";
          const actionDisabled = busy || isFuture;
          const buttonLabel = busy
            ? "Avvio…"
            : notConfigured
              ? "Non ancora configurato"
              : isFuture
                ? "Integrazione futura"
                : program.actionLabel;

          return (
            <li
              key={program.id}
              className={styles.card}
              data-testid={`program-${program.id}`}
              data-status={program.status}
            >
              <div className={styles.cardTop}>
                <span className={styles.icon} aria-hidden>
                  {program.icon}
                </span>
                <div className={styles.meta}>
                  <div className={styles.name}>{program.name}</div>
                  <div
                    className={styles.status}
                    data-status={program.status}
                  >
                    {statusLabel(program.status)}
                  </div>
                </div>
              </div>
              <p className={styles.description}>{program.description}</p>
              <div className={styles.actions}>
                <Button
                  size="small"
                  variant={executable || checkChat ? "primary" : "ghost"}
                  disabled={actionDisabled}
                  onClick={() => void handleAction(program)}
                  aria-label={`${buttonLabel} ${program.name}`}
                  data-testid={`program-action-${program.id}`}
                >
                  {buttonLabel}
                </Button>
              </div>
              {feedback[program.id] && (
                <p
                  className={styles.feedback}
                  data-testid={`program-feedback-${program.id}`}
                  role="status"
                >
                  {feedback[program.id]}
                </p>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
