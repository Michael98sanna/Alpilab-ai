import type { BrainSource } from "../../api/aiBrain";
import styles from "./BrainResponseBadge.module.css";

interface BrainResponseBadgeProps {
  source: BrainSource;
  provider: string;
  confidence: number;
  similarCasesCount: number;
  lowAccuracyWarning?: boolean;
}

const SOURCE_LABELS: Record<BrainSource, { icon: string; label: string }> = {
  local_kb: { icon: "🧠", label: "Dalla nostra esperienza" },
  hybrid: { icon: "🔀", label: "Esperienza + AI" },
  online: { icon: "☁️", label: "AI online" },
};

export function BrainResponseBadge({
  source,
  provider,
  confidence,
  similarCasesCount,
  lowAccuracyWarning = false,
}: BrainResponseBadgeProps) {
  const meta = SOURCE_LABELS[source] ?? SOURCE_LABELS.online;
  return (
    <div className={styles.badge} data-testid="brain-response-badge">
      <span className={styles.icon}>{meta.icon}</span>
      <span className={styles.label}>{meta.label}</span>
      <span className={styles.meta}>
        {provider} · {(confidence * 100).toFixed(0)}%
        {similarCasesCount > 0 && ` · ${similarCasesCount} casi simili`}
      </span>
      {lowAccuracyWarning && (
        <span className={styles.warning}>Accuratezza storica bassa su questo tipo</span>
      )}
    </div>
  );
}
