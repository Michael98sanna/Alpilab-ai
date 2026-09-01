import { useState } from "react";
import type { DetectedDevice } from "../../types";
import { deviceDisplayName } from "../../utils/deviceKind";
import { Button } from "../ui/Button";
import styles from "./AddDeviceDialog.module.css";

type Tab = "connected" | "manual";

interface AddDeviceDialogProps {
  detectedDevices: DetectedDevice[];
  existingDeviceIds: string[];
  onAssociateDetected: (deviceId: string) => void;
  onAddManual: (brand: string, model: string) => void;
  onClose: () => void;
}

function detectedLabel(device: DetectedDevice): string {
  return deviceDisplayName(device.brand, device.model, device.id);
}

export function AddDeviceDialog({
  detectedDevices,
  existingDeviceIds,
  onAssociateDetected,
  onAddManual,
  onClose,
}: AddDeviceDialogProps) {
  const [tab, setTab] = useState<Tab>(
    detectedDevices.length > 0 ? "connected" : "manual",
  );
  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [error, setError] = useState<string | null>(null);

  const availableDetected = detectedDevices.filter(
    (device) => !existingDeviceIds.includes(device.id),
  );

  const handleManualSubmit = () => {
    const brandText = brand.trim();
    const modelText = model.trim();
    if (!brandText && !modelText) {
      setError("Inserisci almeno marca o modello.");
      return;
    }
    setError(null);
    onAddManual(brandText, modelText);
  };

  return (
    <div className={styles.backdrop} role="presentation" onClick={onClose}>
      <div
        className={styles.dialog}
        role="dialog"
        aria-labelledby="add-device-title"
        data-testid="add-device-dialog"
        onClick={(event) => event.stopPropagation()}
      >
        <div className={styles.header}>
          <h2 id="add-device-title" className={styles.title}>
            Aggiungi dispositivo
          </h2>
          <p className={styles.hint}>
            Collega un device rilevato dal PC oppure inserisci marca e modello manualmente.
          </p>
        </div>

        <div className={styles.tabs}>
          <button
            type="button"
            className={`${styles.tab} ${tab === "connected" ? styles.tabActive : ""}`}
            onClick={() => setTab("connected")}
          >
            Collegato al PC
          </button>
          <button
            type="button"
            className={`${styles.tab} ${tab === "manual" ? styles.tabActive : ""}`}
            onClick={() => setTab("manual")}
          >
            Manuale
          </button>
        </div>

        <div className={styles.body}>
          {tab === "connected" && (
            <>
              {availableDetected.length === 0 ? (
                <p className={styles.empty}>
                  Nessun nuovo dispositivo USB rilevato. Usa la scheda Manuale oppure collega
                  un device al PC.
                </p>
              ) : (
                <div className={styles.deviceList}>
                  {availableDetected.map((device) => (
                    <div key={device.id} className={styles.deviceItem}>
                      <div className={styles.deviceLabel}>
                        <span className={styles.deviceName}>{detectedLabel(device)}</span>
                        <span className={styles.deviceMeta}>{device.id}</span>
                      </div>
                      <Button
                        variant="primary"
                        size="small"
                        onClick={() => onAssociateDetected(device.id)}
                      >
                        Aggiungi
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {tab === "manual" && (
            <>
              <div className={styles.field}>
                <label htmlFor="manual-brand">Marca</label>
                <input
                  id="manual-brand"
                  value={brand}
                  onChange={(event) => setBrand(event.target.value)}
                  placeholder="Es. Apple, Samsung"
                />
              </div>
              <div className={styles.field}>
                <label htmlFor="manual-model">Modello</label>
                <input
                  id="manual-model"
                  value={model}
                  onChange={(event) => setModel(event.target.value)}
                  placeholder="Es. iPhone 14 Pro"
                />
              </div>
              {error && <p className={styles.error}>{error}</p>}
            </>
          )}
        </div>

        <div className={styles.footer}>
          <Button variant="ghost" onClick={onClose}>
            Annulla
          </Button>
          {tab === "manual" && (
            <Button variant="primary" onClick={handleManualSubmit}>
              Crea scheda
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
