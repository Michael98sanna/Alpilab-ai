import type { ReactNode } from "react";
import styles from "./BottomSheet.module.css";

interface BottomSheetProps {
  title: string;
  onClose: () => void;
  children: ReactNode;
  testId?: string;
}

export function BottomSheet({ title, onClose, children, testId }: BottomSheetProps) {
  return (
    <>
      <div
        className={styles.overlay}
        onClick={onClose}
        aria-hidden="true"
        data-testid={testId ? `${testId}-overlay` : undefined}
      />
      <div
        className={styles.sheet}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        data-testid={testId}
      >
        <div className={styles.handle} aria-hidden="true" />
        <div className={styles.header}>
          <span className={styles.title}>{title}</span>
          <button type="button" className={styles.closeBtn} onClick={onClose}>
            Chiudi
          </button>
        </div>
        <div className={styles.body}>{children}</div>
      </div>
    </>
  );
}
