import type { DiagnosticCard } from "../../api/diagnosticCards";
import { Button } from "../ui/Button";
import styles from "./RepairCardsSidebar.module.css";

interface RepairCardsSidebarProps {
  cards: DiagnosticCard[];
  activeCardId: string | null;
  loading?: boolean;
  onSelectCard: (card: DiagnosticCard) => void;
  onAddDevice: () => void;
}

export function RepairCardsSidebar({
  cards,
  activeCardId,
  loading = false,
  onSelectCard,
  onAddDevice,
}: RepairCardsSidebarProps) {
  return (
    <aside className={styles.sidebar} data-testid="repair-cards-sidebar">
      <div className={styles.header}>
        <h2 className={styles.title}>Schede</h2>
        <p className={styles.subtitle}>Una conversazione per dispositivo</p>
      </div>

      <div className={styles.list}>
        {loading && cards.length === 0 && (
          <p className={styles.empty}>Caricamento schede...</p>
        )}
        {!loading && cards.length === 0 && (
          <p className={styles.empty}>Nessuna scheda — aggiungi un dispositivo.</p>
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
            <span className={styles.cardMeta}>{card.device_id}</span>
            {card.current_symptom && (
              <span className={styles.cardSymptom}>{card.current_symptom}</span>
            )}
          </button>
        ))}
      </div>

      <div className={styles.footer}>
        <Button variant="primary" className={styles.addBtn} onClick={onAddDevice}>
          + Dispositivo
        </Button>
      </div>
    </aside>
  );
}
