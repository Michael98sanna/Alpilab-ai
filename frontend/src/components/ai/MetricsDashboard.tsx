import { useEffect, useState } from "react";

import {

  fetchBrainMetrics,

  fetchProviderMetrics,

  fetchProviderStatus,

  type BrainMetrics,

  type KbMaturity,

} from "../../api/aiBrain";

import styles from "./MetricsDashboard.module.css";



const STAGE_LABELS: Record<string, string> = {

  cold: "Fredda",

  warming: "In crescita",

  mature: "Matura",

};



const EMPTY_MATURITY: KbMaturity = {

  indexed_cases: 0,

  cases_by_type: {},

  local_hit_rate_30d: 0,

  estimated_api_calls_saved: 0,

  maturity_stage: "cold",

};



export function MetricsDashboard() {

  const [metrics, setMetrics] = useState<BrainMetrics | null>(null);

  const [kbMode, setKbMode] = useState<string>("disabled");

  const [providers, setProviders] = useState<

    Array<{

      provider: string;

      diagnosis_type: string;

      accuracy: number;

      total: number;

      correct: number;

      avg_latency_ms: number;

    }>

  >([]);

  const [warning, setWarning] = useState<string | null>(null);



  useEffect(() => {

    let cancelled = false;

    const load = () => {

      void Promise.allSettled([

        fetchBrainMetrics(),

        fetchProviderMetrics(),

        fetchProviderStatus(),

      ]).then(([metricsResult, providersResult, statusResult]) => {

        if (cancelled) return;



        const warnings: string[] = [];



        if (metricsResult.status === "fulfilled") {

          setMetrics(metricsResult.value);

        } else {

          setMetrics({

            global_accuracy: 0,

            by_type: [],

            kb_maturity: EMPTY_MATURITY,

          });

          warnings.push("Metriche Brain non disponibili");

        }



        if (providersResult.status === "fulfilled") {

          const rows = providersResult.value.providers;

          setProviders(Array.isArray(rows) ? rows : []);

          if (!Array.isArray(rows)) {

            warnings.push("Formato metriche provider non valido");

          }

        } else {

          setProviders([]);

          warnings.push("Metriche provider non disponibili");

        }



        if (statusResult.status === "fulfilled") {

          setKbMode(statusResult.value.kb?.mode ?? "disabled");

        } else {

          setKbMode("disabled");

        }



        setWarning(warnings.length > 0 ? warnings.join(" · ") : null);

      });

    };

    load();

    const timer = window.setInterval(load, 30000);

    return () => {

      cancelled = true;

      window.clearInterval(timer);

    };

  }, []);



  if (!metrics) {

    return <p className={styles.loading}>Caricamento metriche…</p>;

  }



  const globalAccuracy = Number(

    metrics.global_accuracy ??

      (metrics.accuracy !== undefined ? metrics.accuracy : 0),

  ) || 0;



  const maturity: KbMaturity = metrics.kb_maturity ?? EMPTY_MATURITY;

  const stage = maturity.maturity_stage ?? "cold";



  return (

    <section className={styles.dashboard} data-testid="brain-metrics-dashboard">

      <h2 className={styles.title}>Apprendimento ALPILAB Brain</h2>



      {warning && <p className={styles.warningBanner}>{warning}</p>}



      {kbMode === "hash" && (

        <p className={styles.hashWarning} data-testid="kb-hash-warning">

          Ricerca semantica non attiva — installa sentence-transformers per abilitare

          la memoria locale

        </p>

      )}



      <div className={styles.maturitySection} data-testid="kb-maturity-section">

        <h3 className={styles.subtitle}>Maturità memoria</h3>

        <div className={styles.maturityCard}>

          <div className={styles.maturityRow}>

            <span>Casi indicizzati</span>

            <strong>{maturity.indexed_cases}</strong>

          </div>

          <div className={styles.maturityRow}>

            <span>Stadio</span>

            <span

              className={`${styles.stageBadge} ${styles[`stage_${stage}`] ?? ""}`}

              data-testid="maturity-stage-badge"

            >

              {STAGE_LABELS[stage] ?? stage}

            </span>

          </div>

          <div className={styles.maturityRow}>

            <span>Hit rate locale (30 gg)</span>

            <strong>{((Number(maturity.local_hit_rate_30d) || 0) * 100).toFixed(1)}%</strong>

          </div>

          <div className={styles.maturityRow}>

            <span>Chiamate API risparmiate (stima)</span>

            <strong>{maturity.estimated_api_calls_saved}</strong>

          </div>

          {stage === "cold" && (

            <p className={styles.coldMessage} data-testid="kb-cold-message">

              Il sistema impara dalle tue conferme: servono almeno 10 casi confermati

              prima che la memoria locale diventi efficace. Continua a confermare le

              diagnosi corrette dopo ogni riparazione.

            </p>

          )}

        </div>

      </div>



      <div className={styles.globalCard}>

        <span className={styles.globalLabel}>Accuratezza globale</span>

        <strong className={styles.globalValue}>{(globalAccuracy * 100).toFixed(1)}%</strong>

      </div>



      <div className={styles.grid}>

        {(metrics.by_type ?? []).map((row) => (

          <div key={row.diagnosis_type} className={styles.typeCard}>

            <span className={styles.typeName}>{row.diagnosis_type}</span>

            <strong>{((Number(row.accuracy) || 0) * 100).toFixed(0)}%</strong>

            <small>

              {row.correct}/{row.total} casi

            </small>

          </div>

        ))}

      </div>



      <h3 className={styles.subtitle}>Provider</h3>

      <table className={styles.table}>

        <thead>

          <tr>

            <th>Provider</th>

            <th>Tipo</th>

            <th>Accuratezza</th>

            <th>Casi</th>

            <th>Latency</th>

          </tr>

        </thead>

        <tbody>

          {providers.length === 0 && (

            <tr>

              <td colSpan={5}>Nessun dato provider ancora.</td>

            </tr>

          )}

          {providers.map((row) => (

            <tr key={`${row.provider}-${row.diagnosis_type}`}>

              <td>{row.provider}</td>

              <td>{row.diagnosis_type}</td>

              <td>{((Number(row.accuracy) || 0) * 100).toFixed(0)}%</td>

              <td>

                {row.correct}/{row.total}

              </td>

              <td>{(row.avg_latency_ms ?? 0).toFixed(0)} ms</td>

            </tr>

          ))}

        </tbody>

      </table>

    </section>

  );

}

