import { useCallback, useEffect, useState } from "react";
import {
  archiveDiagnosticCard,
  fetchActiveDiagnosticCards,
  fetchDiagnosticCard,
  type DiagnosticCard,
  type DiagnosticCardSummary,
  type DiagnosticMessage,
} from "../../api/diagnosticCards";
import { AIResponseMeta } from "../ai/AIResponseMeta";
import { FeedbackPanel } from "../ai/FeedbackPanel";
import type { BrainSource } from "../../api/aiBrain";
import styles from "./DiagnosticCardPanel.module.css";

interface DiagnosticCardPanelProps {
  sessionId: string;
  cards?: DiagnosticCard[];
  selectedCardId?: string | null;
  layout?: "tabs" | "page";
}

export function DiagnosticCardPanel({
  sessionId,
  cards: externalCards,
  selectedCardId = null,
  layout = "tabs",
}: DiagnosticCardPanelProps) {
  const [activeCards, setActiveCards] = useState<DiagnosticCard[]>(externalCards ?? []);
  const [selectedCard, setSelectedCard] = useState<DiagnosticCard | null>(null);
  const [summary, setSummary] = useState<DiagnosticCardSummary | null>(null);
  const [conversation, setConversation] = useState<DiagnosticMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(layout === "page");

  const cards = externalCards ?? activeCards;

  const loadActiveCards = useCallback(async () => {
    if (externalCards) {
      return;
    }
    try {
      setError(null);
      const nextCards = await fetchActiveDiagnosticCards(sessionId);
      setActiveCards(nextCards);
    } catch (err) {
      console.error("Error loading cards:", err);
      setError("Impossibile caricare le schede diagnostiche.");
    }
  }, [externalCards, sessionId]);

  useEffect(() => {
    if (externalCards) {
      setActiveCards(externalCards);
    }
  }, [externalCards]);

  useEffect(() => {
    if (externalCards) {
      return;
    }
    void loadActiveCards();
    const timer = window.setInterval(() => {
      void loadActiveCards();
    }, 15000);
    return () => window.clearInterval(timer);
  }, [externalCards, loadActiveCards]);

  useEffect(() => {
    if (layout === "page") {
      const match = cards.find((card) => card.id === selectedCardId) ?? null;
      setSelectedCard(match);
      setExpanded(true);
      return;
    }
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
      setExpanded(false);
    }
  }, [cards, layout, selectedCardId]);

  useEffect(() => {
    if (!selectedCard || !expanded) {
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
        setError(null);
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
  }, [selectedCard?.id, expanded]);

  const handleArchive = async (cardId: string, outcome: string) => {
    try {
      await archiveDiagnosticCard(cardId, {
        outcome,
        final_diagnosis: summary?.hypothesis || "TBD",
        solution: "See conversation history",
      });
      if (!externalCards) {
        await loadActiveCards();
      }
    } catch (err) {
      console.error("Error archiving card:", err);
      setError("Archiviazione non riuscita.");
    }
  };

  if (layout === "page") {
    if (cards.length === 0) {
      return (
        <section className={styles.pageEmpty} data-testid="diagnostics-card-empty">
          <h2 className={styles.pageEmptyTitle}>Nessuna scheda diagnostica</h2>
          <p className={styles.pageEmptyHint}>
            Aggiungi un dispositivo dal pannello a sinistra oppure inizia dalla chat e
            associa un device in seguito.
          </p>
        </section>
      );
    }

    if (!selectedCardId) {
      return (
        <section className={styles.pageEmpty} data-testid="diagnostics-card-empty">
          <h2 className={styles.pageEmptyTitle}>Seleziona una scheda</h2>
          <p className={styles.pageEmptyHint}>
            Scegli un dispositivo dal pannello schede per vedere sintomi, ipotesi e
            conversazione diagnostica.
          </p>
        </section>
      );
    }

    return (
      <div className={styles.pageContainer} data-testid="diagnostics-card-panel">
        {error && <div className={styles.error}>{error}</div>}
        {loading && <div className={styles.loading}>Caricamento scheda…</div>}
        {!loading && summary && selectedCard && (
          <CardDetailContent
            summary={summary}
            conversation={conversation}
            selectedCard={selectedCard}
            onArchive={handleArchive}
          />
        )}
      </div>
    );
  }

  if (cards.length === 0) {
    return null;
  }

  return (
    <div className={styles.container}>
      <div className={styles.tabBar}>
        {cards.map((card) => (
          <div
            key={card.id}
            className={`${styles.tab} ${selectedCard?.id === card.id ? styles.active : ""}`}
            onClick={() => {
              setSelectedCard(card);
              setExpanded(true);
            }}
            role="tab"
            tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                setSelectedCard(card);
                setExpanded(true);
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
        <button
          type="button"
          className={styles.toggleBtn}
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "Nascondi" : "Dettagli"}
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {expanded && selectedCard && !loading && summary && (
        <CardDetailContent
          summary={summary}
          conversation={conversation}
          selectedCard={selectedCard}
          onArchive={handleArchive}
        />
      )}

      {expanded && loading && <div className={styles.loading}>⏳ Caricamento...</div>}
    </div>
  );
}

function CardDetailContent({
  summary,
  conversation,
  selectedCard,
  onArchive,
}: {
  summary: DiagnosticCardSummary;
  conversation: DiagnosticMessage[];
  selectedCard: DiagnosticCard;
  onArchive: (cardId: string, outcome: string) => void;
}) {
  return (
    <div className={styles.content}>
      <div className={styles.section}>
        <h3>{selectedCard.device_name}</h3>
        <div className={styles.summaryGrid}>
          <div className={styles.summaryItem}>
            <strong>Sintomo</strong>
            <p>{summary.current_symptom || "—"}</p>
          </div>
          <div className={styles.summaryItem}>
            <strong>Ipotesi</strong>
            <p>{summary.hypothesis || "—"}</p>
          </div>
          <div className={styles.summaryItem}>
            <strong>Confidenza</strong>
            <p>{((summary.confidence ?? 0) * 100).toFixed(0)}%</p>
          </div>
          <div className={styles.summaryItem}>
            <strong>Fase</strong>
            <p>{summary.diagnostic_stage}</p>
          </div>
          <div className={styles.summaryItem}>
            <strong>Messaggi</strong>
            <p>{summary.messages_count}</p>
          </div>
          <div className={styles.summaryItem}>
            <strong>Aggiornato</strong>
            <p>{new Date(summary.updated).toLocaleString("it-IT")}</p>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3>Conversazione diagnostica</h3>
        <div className={styles.messages}>
          {conversation.length === 0 && (
            <p className={styles.emptyInline}>Nessun messaggio salvato per questo device.</p>
          )}
          {conversation.map((msg) => {
            const brain = msg.tool_calls?.brain;
            const source = (brain?.source ?? "online") as BrainSource;
            return (
            <div
              key={`${msg.timestamp}-${msg.role}-${(msg.content ?? "").slice(0, 24)}`}
              className={`${styles.message} ${styles[msg.role] ?? ""}`}
            >
              <strong>{msg.role === "user" ? "Tu" : "ALPILAB"}</strong>
              <p>{msg.content}</p>
              {msg.role === "assistant" && brain && (
                <>
                  <AIResponseMeta
                    source={source}
                    provider={brain.provider ?? "unknown"}
                    model={brain.model}
                    confidence={brain.confidence ?? 0}
                    latencyMs={brain.latency_ms}
                    kbHits={brain.kb_hits}
                    usedOnline={brain.used_online}
                    lowAccuracyWarning={brain.low_accuracy_warning}
                    kbMode={brain.kb_mode}
                    localModel={brain.local_model}
                    validation={brain.validation}
                  />
                  <FeedbackPanel
                    cardId={selectedCard.id}
                    provider={brain.provider}
                    preConfidence={brain.confidence}
                    knowledgeEntryId={brain.knowledge_entry_id}
                    source={source}
                  />
                </>
              )}
              <small>{new Date(msg.timestamp).toLocaleString("it-IT")}</small>
            </div>
          );
          })}
        </div>
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.btnSuccess}
          onClick={() => void onArchive(selectedCard.id, "success")}
        >
          Riparazione riuscita
        </button>
        <button
          type="button"
          className={styles.btnFail}
          onClick={() => void onArchive(selectedCard.id, "failed")}
        >
          Riparazione non riuscita
        </button>
      </div>
    </div>
  );
}
