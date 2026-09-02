import type { BrainSource } from "../../api/aiBrain";
import styles from "./AIResponseMeta.module.css";

export type KbMode = "semantic" | "hash" | "disabled";

export interface ValidationMeta {
  performed?: boolean;
  agreed?: boolean | null;
  overridden?: boolean;
}

interface AIResponseMetaProps {
  source: BrainSource;
  provider: string;
  model?: string;
  confidence: number;
  latencyMs?: number;
  kbHits?: number;
  usedOnline?: boolean;
  lowAccuracyWarning?: boolean;
  kbMode?: KbMode;
  localModel?: boolean;
  validation?: ValidationMeta;
}

export function AIResponseMeta({
  source,
  provider,
  model,
  confidence,
  latencyMs,
  kbHits = 0,
  usedOnline = source !== "local_kb",
  lowAccuracyWarning = false,
  kbMode = "disabled",
  localModel = false,
  validation,
}: AIResponseMetaProps) {
  const showLocalBadge = source === "local_kb" && kbMode === "semantic";
  const showLocalModelBadge = localModel || provider === "ollama";
  const showOnlineBadge =
    !showLocalModelBadge && (kbMode === "hash" || usedOnline || source === "online");
  const overridden = validation?.overridden === true;

  return (
    <div className={styles.meta} data-testid="ai-response-meta">
      {showLocalBadge && (
        <span className={`${styles.badge} ${styles.badgeLocal}`}>
          📚 da conoscenza locale
        </span>
      )}
      {!showLocalBadge && showOnlineBadge && (
        <span className={`${styles.badge} ${styles.badgeOnline}`}>🌐 online</span>
      )}
      {showLocalModelBadge && (
        <span
          className={`${styles.badge} ${styles.badgeLocalModel}`}
          data-testid="local-model-badge"
        >
          🏠 modello locale — affidabilità ridotta
        </span>
      )}
      {!showLocalBadge && !showOnlineBadge && !showLocalModelBadge && source === "hybrid" && (
        <span className={`${styles.badge} ${styles.badgeOnline}`}>🔀 ibrido</span>
      )}
      {overridden && (
        <span className={styles.warning} data-testid="validation-override-badge">
          ⚠️ caso locale corretto online
        </span>
      )}
      <span className={styles.details}>
        {provider}
        {model ? ` · ${model}` : ""} · {(confidence * 100).toFixed(0)}%
        {latencyMs !== undefined ? ` · ${latencyMs} ms` : ""}
        {kbHits > 0 ? ` · ${kbHits} KB` : ""}
      </span>
      {lowAccuracyWarning && (
        <span className={styles.warning}>
          Accuratezza storica bassa su questo tipo di guasto
        </span>
      )}
    </div>
  );
}
