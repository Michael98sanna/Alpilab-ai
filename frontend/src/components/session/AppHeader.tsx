import styles from "./AppHeader.module.css";

interface AppHeaderProps {
  onVoiceClick?: () => void;
}

export function AppHeader({ onVoiceClick }: AppHeaderProps) {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>ALPILAB AI</div>
      <div className={styles.right}>
        <button
          type="button"
          className={styles.micBtn}
          aria-label="Attiva microfono"
          onClick={onVoiceClick}
        >
          🎙️
        </button>
        <div className={styles.user}>
          <span className={styles.dot} aria-hidden="true" />
          <span>Michael</span>
        </div>
      </div>
    </header>
  );
}
