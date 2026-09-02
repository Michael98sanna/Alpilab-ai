import { useState } from "react";
import {
  submitBrainFeedback,
  submitRepairOutcome,
  type BrainSource,
} from "../../api/aiBrain";
import styles from "./FeedbackPanel.module.css";

interface FeedbackPanelProps {
  cardId: string;
  provider?: string;
  preConfidence?: number;
  knowledgeEntryId?: string | null;
  source?: BrainSource;
}

export function FeedbackPanel({
  cardId,
  provider,
  preConfidence = 0,
  knowledgeEntryId,
  source,
}: FeedbackPanelProps) {
  const [correction, setCorrection] = useState("");
  const [showCorrection, setShowCorrection] = useState(false);
  const [confirmationId, setConfirmationId] = useState<string | null>(null);
  const [step, setStep] = useState<"feedback" | "outcome" | "done">("feedback");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function sendFeedback(feedback: "confirmed" | "corrected" | "rejected") {
    setBusy(true);
    setError(null);
    try {
      const result = await submitBrainFeedback(cardId, {
        feedback,
        correction_text: feedback === "corrected" ? correction.trim() : undefined,
        provider,
        pre_confidence: preConfidence,
        knowledge_entry_id: knowledgeEntryId,
      });
      setConfirmationId(result.confirmation_id);
      setStep("outcome");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore feedback");
    } finally {
      setBusy(false);
    }
  }

  async function sendOutcome(outcome: "success" | "partial" | "failed") {
    if (!confirmationId) return;
    setBusy(true);
    setError(null);
    try {
      await submitRepairOutcome(confirmationId, outcome);
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore esito");
    } finally {
      setBusy(false);
    }
  }

  if (step === "done") {
    return (
      <p className={styles.done} data-testid="feedback-done">
        Grazie — il caso è stato registrato per migliorare le diagnosi future.
      </p>
    );
  }

  if (step === "outcome") {
    return (
      <div className={styles.panel} data-testid="feedback-outcome">
        <p className={styles.prompt}>Esito della riparazione?</p>
        <div className={styles.actions}>
          <button type="button" disabled={busy} onClick={() => void sendOutcome("success")}>
            ✅ Riuscita
          </button>
          <button type="button" disabled={busy} onClick={() => void sendOutcome("partial")}>
            ⚠️ Parziale
          </button>
          <button type="button" disabled={busy} onClick={() => void sendOutcome("failed")}>
            ❌ Non riuscita
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.panel} data-testid="feedback-panel">
      <p className={styles.prompt}>Questa diagnosi è corretta?</p>
      <div className={styles.actions}>
        <button type="button" disabled={busy} onClick={() => void sendFeedback("confirmed")}>
          ✅ Corretto
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => setShowCorrection((value) => !value)}
        >
          ❌ Non è così
        </button>
      </div>
      {showCorrection && (
        <div className={styles.correction}>
          <textarea
            value={correction}
            onChange={(event) => setCorrection(event.target.value)}
            placeholder="Scrivi la diagnosi corretta…"
            rows={3}
          />
          <button
            type="button"
            disabled={busy || !correction.trim()}
            onClick={() => void sendFeedback("corrected")}
          >
            Invia correzione
          </button>
          <button type="button" disabled={busy} onClick={() => void sendFeedback("rejected")}>
            Rifiuta senza correzione
          </button>
        </div>
      )}
      {error && <p className={styles.error}>{error}</p>}
    </div>
  );
}
