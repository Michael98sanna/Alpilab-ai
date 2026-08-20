import { useCallback, useState, type MouseEvent, type RefObject } from "react";
import type { ChatMessage } from "../../types";
import {
  getDomSelectionText,
  selectElementText,
  writeClipboardText,
} from "../../utils/clipboard";
import { shouldUseAppContextMenu } from "../../utils/pointerEnv";
import { ChatContextMenu } from "./ChatContextMenu";
import styles from "./ChatPanel.module.css";

interface ChatTimelineProps {
  messages: ChatMessage[];
  containerRef: RefObject<HTMLDivElement>;
  onScroll: () => void;
  showNewMessages: boolean;
  onJumpToLatest: () => void;
}

type MenuState = {
  x: number;
  y: number;
  selectedText: string;
  contentEl: HTMLElement | null;
};

export function ChatTimeline({
  messages,
  containerRef,
  onScroll,
  showNewMessages,
  onJumpToLatest,
}: ChatTimelineProps) {
  const chatMessages = messages.filter((m) => m.role !== "status");
  const [menu, setMenu] = useState<MenuState | null>(null);

  const closeMenu = useCallback(() => setMenu(null), []);

  function handleMessageContextMenu(
    e: MouseEvent<HTMLDivElement>,
    contentEl: HTMLElement | null,
  ) {
    if (!shouldUseAppContextMenu()) return;
    e.preventDefault();
    setMenu({
      x: e.clientX,
      y: e.clientY,
      selectedText: getDomSelectionText(),
      contentEl,
    });
  }

  return (
    <div className={styles.timelineWrap}>
      <div
        ref={containerRef}
        className={styles.list}
        role="log"
        aria-label="Conversazione"
        onScroll={onScroll}
        data-testid="chat-timeline"
      >
        {chatMessages.map((msg) => (
          <div
            key={msg.id}
            className={`${styles.message} ${styles[msg.role]}`}
            data-testid={`message-${msg.role}`}
            data-selectable="true"
            onContextMenu={(e) => {
              const content = e.currentTarget.querySelector(
                "[data-testid='message-content']",
              ) as HTMLElement | null;
              handleMessageContextMenu(e, content);
            }}
          >
            <span
              className={styles.content}
              data-testid="message-content"
            >
              {msg.content}
            </span>
            <span className={styles.time}>{msg.timestamp}</span>
          </div>
        ))}
      </div>

      {showNewMessages && (
        <button
          type="button"
          className={styles.newMessagesBtn}
          onClick={onJumpToLatest}
          aria-label="Nuovi messaggi"
        >
          Nuovi messaggi ↓
        </button>
      )}

      {menu && (
        <ChatContextMenu
          x={menu.x}
          y={menu.y}
          onClose={closeMenu}
          testId="message-context-menu"
          items={[
            {
              id: "copy",
              label: "Copia",
              disabled: !menu.selectedText.trim(),
              onSelect: () => {
                void writeClipboardText(menu.selectedText);
              },
            },
            {
              id: "select-all",
              label: "Seleziona tutto",
              disabled: !menu.contentEl,
              onSelect: () => {
                if (menu.contentEl) selectElementText(menu.contentEl);
              },
            },
          ]}
        />
      )}
    </div>
  );
}
