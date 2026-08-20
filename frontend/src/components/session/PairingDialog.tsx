import { useState } from "react";
import { getApiBaseUrl } from "../../config/env";
import { Button } from "../ui/Button";
import styles from "./PairingDialog.module.css";

interface PairingStartResponse {
  code: string;
  expires_at?: string;
  ttl_seconds?: number;
}

export function PairingDialog({ onClose }: { onClose: () => void }) {
  const [code, setCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function startPairing() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/v1/pairing/start`, {
        method: "POST",
      });
      if (!res.ok) {
        setError("Pairing non disponibile.");
        return;
      }
      const data = (await res.json()) as PairingStartResponse;
      setCode(data.code);
    } catch {
      setError("Local Hub non raggiungibile.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.backdrop} role="presentation" onClick={onClose}>
      <div
        className={styles.dialog}
        role="dialog"
        aria-labelledby="pairing-title"
        data-testid="pairing-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="pairing-title" className={styles.title}>
          Collega dispositivo
        </h2>
        <p className={styles.hint}>
          Sul telefono apri ALPILAB AI, trova Alpilab Negozio e inserisci questo codice.
        </p>
        {code ? (
          <p className={styles.code} data-testid="pairing-code">
            {code}
          </p>
        ) : (
          <Button variant="primary" onClick={() => void startPairing()} disabled={busy}>
            Genera codice
          </Button>
        )}
        {error ? (
          <p className={styles.error} data-testid="pairing-error">
            {error}
          </p>
        ) : null}
        <div className={styles.actions}>
          <Button variant="ghost" size="small" onClick={onClose}>
            Chiudi
          </Button>
        </div>
      </div>
    </div>
  );
}
