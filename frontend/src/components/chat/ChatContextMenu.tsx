import { useEffect, useRef } from "react";
import styles from "./ChatContextMenu.module.css";

export type ContextMenuItem = {
  id: string;
  label: string;
  disabled?: boolean;
  onSelect: () => void;
};

type ChatContextMenuProps = {
  x: number;
  y: number;
  items: ContextMenuItem[];
  onClose: () => void;
  testId?: string;
};

export function ChatContextMenu({
  x,
  y,
  items,
  onClose,
  testId = "chat-context-menu",
}: ChatContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    function onPointer(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onPointer);
    };
  }, [onClose]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const maxX = window.innerWidth - rect.width - 8;
    const maxY = window.innerHeight - rect.height - 8;
    el.style.left = `${Math.max(8, Math.min(x, maxX))}px`;
    el.style.top = `${Math.max(8, Math.min(y, maxY))}px`;
  }, [x, y]);

  return (
    <div
      ref={ref}
      className={styles.menu}
      style={{ left: x, top: y }}
      role="menu"
      data-testid={testId}
    >
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          role="menuitem"
          className={styles.item}
          disabled={item.disabled}
          data-testid={`context-menu-${item.id}`}
          onClick={() => {
            if (item.disabled) return;
            item.onSelect();
            onClose();
          }}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
