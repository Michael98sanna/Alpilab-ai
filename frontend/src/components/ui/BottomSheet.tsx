import type { ReactNode } from "react";
import { useSheetDrag } from "../../hooks/useSheetDrag";
import styles from "./BottomSheet.module.css";

interface BottomSheetProps {
  title: string;
  onClose: () => void;
  children: ReactNode;
  testId?: string;
  swipeHandlers?: {
    onTouchStart: (e: React.TouchEvent) => void;
    onTouchMove: (e: React.TouchEvent) => void;
    onTouchEnd: (e: React.TouchEvent) => void;
  };
}

export function BottomSheet({
  title,
  onClose,
  children,
  testId,
  swipeHandlers,
}: BottomSheetProps) {
  const { dragY, dragging, dismissThreshold, handlers: dragHandlers } =
    useSheetDrag(onClose);

  const sheetStyle =
    dragY > 0
      ? {
          transform: `translateY(${dragY}px)`,
          transition: dragging ? "none" : "transform 200ms var(--ease-out)",
        }
      : undefined;

  return (
    <>
      <div
        className={styles.overlay}
        onClick={onClose}
        aria-hidden="true"
        data-testid={testId ? `${testId}-overlay` : undefined}
        {...(swipeHandlers ?? {})}
      />
      <div
        className={styles.sheet}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        data-testid={testId}
        style={sheetStyle}
        {...(swipeHandlers ?? {})}
      >
        <div
          className={styles.dragZone}
          data-sheet-drag="true"
          data-testid={testId ? `${testId}-drag-zone` : undefined}
          {...dragHandlers}
        >
          <div className={styles.handle} aria-hidden="true" />
        </div>
        <div className={styles.header}>
          <span className={styles.title}>{title}</span>
          <button type="button" className={styles.closeBtn} onClick={onClose}>
            Chiudi
          </button>
        </div>
        <div
          className={styles.body}
          data-drag-offset={dragY}
          data-dismiss-threshold={dismissThreshold}
        >
          {children}
        </div>
      </div>
    </>
  );
}
