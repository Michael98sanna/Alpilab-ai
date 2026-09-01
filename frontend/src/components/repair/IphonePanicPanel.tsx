import { useState } from "react";
import { executeIphonePanicAnalyze, executeIphonePanicCheck } from "../../api/tools";
import { useAppSession } from "../../realtime/RealtimeProvider";
import styles from "./IphonePanicPanel.module.css";

type PanelState = "idle" | "checking" | "analyzing" | "result" | "error";

interface PanicDeviceInfo {
  device_id?: string;
  device_name?: string;
  ios_version?: string;
  model?: string;
  panic_log_filename?: string;
  status?: string;
  error_message?: string;
}

interface PanicAnalysisInfo {
  panic_type?: string;
  severity?: string;
  confidence?: number;
  component?: string;
  recommendations?: string[];
  cached?: boolean;
  status?: string;
  error_message?: string;
}

export function IphonePanicPanel() {
  const { mode, sessionId, state } = useAppSession();
  const [panelState, setPanelState] = useState<PanelState>("idle");
  const [deviceInfo, setDeviceInfo] = useState<PanicDeviceInfo | null>(null);
  const [analysisResult, setAnalysisResult] = useState<PanicAnalysisInfo | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  const agentId = state.pcAgent?.agentId;
  const agentOnline = Boolean(state.pcAgent?.online);

  const handleCheck = async () => {
    if (mode !== "realtime" || !agentId || !agentOnline) {
      setErrorMsg("PC Agent non disponibile.");
      setPanelState("error");
      return;
    }

    setPanelState("checking");
    setAnalysisResult(null);
    try {
      const response = await executeIphonePanicCheck(sessionId, agentId);
      const payload = response.result as PanicDeviceInfo;
      if (!response.success) {
        setErrorMsg(response.error || "Check failed");
        setPanelState("error");
        return;
      }
      if (payload.status === "success" || payload.status === "no_panic") {
        setDeviceInfo(payload);
        setPanelState("result");
        return;
      }
      setErrorMsg(payload.error_message || "Check failed");
      setPanelState("error");
    } catch (err) {
      setErrorMsg(String(err));
      setPanelState("error");
    }
  };

  const handleAnalyze = async (forceReanalyze = false) => {
    if (mode !== "realtime" || !agentId || !agentOnline) {
      setErrorMsg("PC Agent non disponibile.");
      setPanelState("error");
      return;
    }

    setPanelState("analyzing");
    try {
      const response = await executeIphonePanicAnalyze(sessionId, agentId, {
        force_reanalyze: forceReanalyze,
      });
      const payload = response.result as PanicAnalysisInfo;
      if (!response.success) {
        setErrorMsg(response.error || "Analysis failed");
        setPanelState("error");
        return;
      }
      if (payload.status === "success") {
        setAnalysisResult(payload);
        setPanelState("result");
        return;
      }
      setErrorMsg(payload.error_message || "Analysis failed");
      setPanelState("error");
    } catch (err) {
      setErrorMsg(String(err));
      setPanelState("error");
    }
  };

  return (
    <section className={styles.panel} data-testid="iphone-panic-panel">
      <h3>🍎 iPhone Panic Log</h3>

      {panelState === "idle" && (
        <div className={styles.controls}>
          <button type="button" onClick={handleCheck}>
            Controlla Panic Log
          </button>
        </div>
      )}

      {panelState === "checking" && <p>🔄 Rilevamento iPhone...</p>}
      {panelState === "analyzing" && <p>🤖 Analisi in corso...</p>}

      {panelState === "result" && deviceInfo && (
        <div className={styles.deviceInfo}>
          <p>
            <strong>Device:</strong> {deviceInfo.device_name || "Sconosciuto"}
          </p>
          <p>
            <strong>iOS:</strong> {deviceInfo.ios_version || "Sconosciuto"}
          </p>
          {deviceInfo.model && (
            <p>
              <strong>Modello:</strong> {deviceInfo.model}
            </p>
          )}

          {deviceInfo.panic_log_filename ? (
            <>
              <p>
                <strong>Panic Log:</strong> {deviceInfo.panic_log_filename}
              </p>
              <button type="button" onClick={() => handleAnalyze(false)}>
                Analizza Panic Log
              </button>
            </>
          ) : (
            <p>ℹ️ Nessun panic log trovato</p>
          )}
        </div>
      )}

      {panelState === "result" && analysisResult && (
        <div className={styles.analysisResult}>
          <p>
            <strong>Categoria:</strong> {analysisResult.panic_type}
          </p>
          <p>
            <strong>Severity:</strong> {analysisResult.severity}
          </p>
          <p>
            <strong>Confidence:</strong>{" "}
            {analysisResult.confidence != null
              ? `${(analysisResult.confidence * 100).toFixed(0)}%`
              : "n/d"}
          </p>
          {analysisResult.component && (
            <p>
              <strong>Componente:</strong> {analysisResult.component}
            </p>
          )}
          {analysisResult.cached && <p>♻️ Risultato da cache</p>}

          {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
            <div>
              <strong>Raccomandazioni:</strong>
              <ul>
                {analysisResult.recommendations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          <button type="button" onClick={() => handleAnalyze(true)}>
            Analizza nuovamente
          </button>
          <button type="button" onClick={() => setPanelState("idle")}>
            Nuovo check
          </button>
        </div>
      )}

      {panelState === "error" && (
        <div className={styles.error}>
          <p>❌ {errorMsg}</p>
          <button type="button" onClick={() => setPanelState("idle")}>
            Riprova
          </button>
        </div>
      )}
    </section>
  );
}
