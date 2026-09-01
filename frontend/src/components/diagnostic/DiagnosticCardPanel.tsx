import { useCallback, useEffect, useState } from "react";
import {
  archiveDiagnosticCard,
  createDiagnosticCard,
  fetchActiveDiagnosticCards,
  fetchDiagnosticCard,
  type DiagnosticCard,
  type DiagnosticCardSummary,
  type DiagnosticMessage,
} from "../../api/diagnosticCards";
import styles from "./DiagnosticCardPanel.module.css";

interface DiagnosticCardPanelProps {
  sessionId?: string;
  defaultDeviceId?: string;
  defaultDeviceName?: string;
}

export function DiagnosticCardPanel({
  sessionId,
  defaultDeviceId,
  defaultDeviceName,
}: DiagnosticCardPanelProps) {
  const [activeCards, setActiveCards] = useState<DiagnosticCard[]>([]);
  const [selectedCard, setSelectedCard] = useState<DiagnosticCard | null>(null);
  const [summary, setSummary] = useState<DiagnosticCardSummary | null>(null);
  const [conversation, setConversation] = useState<DiagnosticMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadActiveCards = useCallback(async () => {
    try {
      setError(null);
      const cards = await fetchActiveDiagnosticCards();
      setActiveCards(cards);
      if (cards.length > 0) {
        setSelectedCard((current) => {
          if (current && cards.some((card) => card.id === current.id)) {
            return current;
          }
          return cards[0];
        });
      } else {
        setSelectedCard(null);
        setSummary(null);
        setConversation([]);
      }
    } catch (err) {
      console.error("Error loading cards:", err);
      setError("Impossibile caricare le schede diagnostiche.");
    }
  }, []);

  useEffect(() => {
    void loadActiveCards();
    const timer = window.setInterval(() => {
      void loadActiveCards();
    }, 15000);
    return () => window.clearInterval(timer);
  }, [loadActiveCards]);

  useEffect(() => {
    if (!selectedCard) {
      return;
    }
    let cancelled = false;
    const loadCard = async () => {
      setLoading(true);
      try {
        const data = await fetchDiagnosticCard(selectedCard.id);
        if (cancelled) {
          return;
        }
        setSummary(data.summary);
        setConversation(data.conversation);
        setSelectedCard(data.card);
      } catch (err) {
        console.error("Error loading card:", err);
        if (!cancelled) {
          setError("Impossibile caricare la scheda selezionata.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    void loadCard();
    return () => {
      cancelled = true;
    };
  }, [selectedCard?.id]);

  const handleArchive = async (cardId: string, outcome: string) => {
    try {
      await archiveDiagnosticCard(cardId, {
        outcome,
        final_diagnosis: summary?.hypothesis || "TBD",
        solution: "See conversation history",
      });
      await loadActiveCards();
    } catch (err) {
      console.error("Error archiving card:", err);
      setError("Archiviazione non riuscita.");
    }
  };

  const handleCreateCard = async () => {
    if (!sessionId || !defaultDeviceId) {
      setError("Associa un device per creare una scheda diagnostica.");
      return;
    }
    try {
      await createDiagnosticCard({
        device_id: defaultDeviceId,
        device_name: defaultDeviceName || defaultDeviceId,
        session_id: sessionId,
      });
      await loadActiveCards();
    } catch (err) {
      console.error("Error creating card:", err);
      setError("Creazione scheda non riuscita.");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.tabBar}>
        {activeCards.map((card) => (
          <div
            key={card.id}
            className={`${styles.tab} ${selectedCard?.id === card.id ? styles.active : ""}`}
            onClick={() => setSelectedCard(card)}
            role="tab"
            tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                setSelectedCard(card);
              }
            }}
          >
            <div className={styles.tabContent}>
              <span className={styles.tabTitle}>{card.device_name}</span>
              <span className={styles.tabSubtitle}>{card.device_id}</span>
            </div>
            <button
              type="button"
              className={styles.tabClose}
              aria-label="Archivia scheda"
              onClick={(event) => {
                event.stopPropagation();
                void handleArchive(card.id, "unknown");
              }}
            >
              ✕
            </button>
          </div>
        ))}
        <button type="button" className={styles.newCardBtn} onClick={() => void handleCreateCard()}>
          + Nuovo
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {selectedCard && !loading && summary && (
        <div className={styles.content}>
          <div className={styles.section}>
            <h3>📋 Riassunto Rapido</h3>
            <div className={styles.summaryGrid}>
              <div className={styles.summaryItem}>
                <strong>Sintomo:</strong>
                <p>{summary.current_symptom || "-"}</p>
              </div>
              <div className={styles.summaryItem}>
                <strong>Ipotesi:</strong>
                <p>{summary.hypothesis || "-"}</p>
              </div>
              <div className={styles.summaryItem}>
                <strong>Confidenza:</strong>
                <p>{(summary.confidence * 100).toFixed(0)}%</p>
              </div>
              <div className={styles.summaryItem}>
                <strong>Fase:</strong>
                <p>{summary.diagnostic_stage}</p>
              </div>
              <div className={styles.summaryItem}>
                <strong>Messaggi:</strong>
                <p>{summary.messages_count}</p>
              </div>
              <div className={styles.summaryItem}>
                <strong>Aggiornato:</strong>
                <p>{new Date(summary.updated).toLocaleString("it-IT")}</p>
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <h3>💬 Conversazione</h3>
            <div className={styles.messages}>
              {conversation.length === 0 && (
                <p className={styles.emptyInline}>Nessun messaggio salvato.</p>
              )}
              {conversation.map((msg) => (
                <div
                  key={`${msg.timestamp}-${msg.role}-${msg.content.slice(0, 24)}`}
                  className={`${styles.message} ${styles[msg.role] ?? ""}`}
                >
                  <strong>{msg.role === "user" ? "👤" : "🤖"}</strong>
                  <p>{msg.content}</p>
                  <small>{new Date(msg.timestamp).toLocaleString("it-IT")}</small>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.actions}>
            <button
              type="button"
              className={styles.btnSuccess}
              onClick={() => void handleArchive(selectedCard.id, "success")}
            >
              ✅ Riparazione Riuscita
            </button>
            <button
              type="button"
              className={styles.btnFail}
              onClick={() => void handleArchive(selectedCard.id, "failed")}
            >
              ❌ Riparazione Non Riuscita
            </button>
          </div>
        </div>
      )}

      {loading && <div className={styles.loading}>⏳ Caricamento...</div>}
      {!selectedCard && !loading && (
        <div className={styles.empty}>
          <p>Nessuna scheda attiva — avvia una conversazione o crea una nuova scheda.</p>
        </div>
      )}
    </div>
  );
}
