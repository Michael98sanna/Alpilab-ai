import type { DiagnosticCard } from "../../api/diagnosticCards";
import styles from "./RepairCardsSidebar.module.css";

interface RepairCardsSidebarProps {
  open: boolean;
  cards: DiagnosticCard[];
  activeCardId: string | null;
  loading?: boolean;
  onToggle: () => void;
  onSelectCard: (card: DiagnosticCard) => void;
  onAddDevice: () => void;
}

export function RepairCardsSidebar({
  open,
  cards,
  activeCardId,
  loading = false,
  onToggle,
  onSelectCard,
  onAddDevice,
}: RepairCardsSidebarProps) {
  if (!open) {
    return (
      <aside
        className={`${styles.sidebar} ${styles.collapsed}`}
        data-testid="repair-cards-sidebar"
        aria-label="Schede riparazione"
      >
        <button
          type="button"
          className={styles.expandBtn}
          data-testid="sidebar-expand-btn"
          onClick={onToggle}
          aria-label="Apri schede riparazione"
          title="Apri schede"
        >
          <span className={styles.expandIcon} aria-hidden>
            ›
          </span>
          <span className={styles.expandLabel}>Schede</span>
        </button>
        <button
          type="button"
          className={styles.collapsedAddBtn}
          data-testid="add-device-btn"
          onClick={onAddDevice}
          aria-label="Aggiungi dispositivo"
          title="Aggiungi dispositivo"
        >
          +
        </button>
      </aside>
    );
  }

  return (
    <aside
      className={`${styles.sidebar} ${styles.expanded}`}
      data-testid="repair-cards-sidebar"
      aria-label="Schede riparazione"
    >
      <div className={styles.header}>
        <div className={styles.headerText}>
          <h2 className={styles.title}>In corso</h2>
          <p className={styles.subtitle}>{cards.length} schede</p>
        </div>
        <button
          type="button"
          className={styles.collapseBtn}
          data-testid="sidebar-collapse-btn"
          onClick={onToggle}
          aria-label="Chiudi pannello schede"
          title="Chiudi"
        >
          ‹
        </button>
      </div>

      <div className={styles.list} data-testid="repair-cards-scroller">
        {loading && cards.length === 0 && (
          <p className={styles.empty}>Caricamento…</p>
        )}
        {!loading && cards.length === 0 && (
          <p className={styles.empty}>Nessuna scheda attiva.</p>
        )}
        {cards.map((card) => (
          <button
            key={card.id}
            type="button"
            className={`${styles.cardItem} ${
              activeCardId === card.id ? styles.cardItemActive : ""
            }`}
            onClick={() => onSelectCard(card)}
            data-testid={`repair-card-${card.device_id}`}
          >
            <span className={styles.cardName}>{card.device_name}</span>
            {card.current_symptom ? (
              <span className={styles.cardSymptom}>{card.current_symptom}</span>
            ) : (
              <span className={styles.cardMeta}>{card.device_id}</span>
            )}
          </button>
        ))}
      </div>

      <div className={styles.footer}>
        <button
          type="button"
          className={styles.addBtn}
          data-testid="add-device-btn"
          onClick={onAddDevice}
        >
          + Dispositivo
        </button>
      </div>
    </aside>
  );
}
