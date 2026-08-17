import type { SwipeFeedback } from "../../hooks/useSwipeGesture";
import styles from "./GestureFeedback.module.css";

interface GestureFeedbackProps {
  feedback: SwipeFeedback;
}

const LABELS: Record<NonNullable<SwipeFeedback>, string> = {
  "open-diagnostics": "→ Diagnosi",
  "open-tools": "← Strumenti",
  "close-diagnostics": "← Chiudi",
  "close-tools": "→ Chiudi",
};

export function GestureFeedback({ feedback }: GestureFeedbackProps) {
  if (!feedback) return null;

  const isLeft =
    feedback === "open-diagnostics" || feedback === "close-tools";

  return (
    <div
      className={`${styles.feedback} ${styles.visible} ${isLeft ? styles.left : styles.right}`}
      aria-hidden="true"
      data-testid="gesture-feedback"
    >
      {LABELS[feedback]}
    </div>
  );
}
