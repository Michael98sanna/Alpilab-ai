import type { SwipeDirection } from "../../hooks/useSwipeGesture";
import styles from "./GestureFeedback.module.css";

interface GestureFeedbackProps {
  direction: SwipeDirection;
}

export function GestureFeedback({ direction }: GestureFeedbackProps) {
  if (!direction) return null;

  const isDiagnostics = direction === "diagnostics";

  return (
    <div
      className={`${styles.feedback} ${styles.visible} ${isDiagnostics ? styles.left : styles.right}`}
      aria-hidden="true"
      data-testid="gesture-feedback"
    >
      {isDiagnostics ? "→ Diagnosi" : "← Strumenti"}
    </div>
  );
}
