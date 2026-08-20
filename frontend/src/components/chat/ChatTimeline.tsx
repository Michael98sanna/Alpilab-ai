import { useCallback, useEffect, useState, type MouseEvent, type RefObject } from "react";
import type { ChatMessage } from "../../types";
import { writeClipboardText } from "../../utils/clipboard";
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
  messageId: string;
  fullText: string;
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
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const closeMenu = useCallback(() => setMenu(null), []);

  useEffect(() => {
    if (!copiedId) return;
    const t = window.setTimeout(() => setCopiedId(null), 1500);
    return () => window.clearTimeout(t);
  }, [copiedId]);

  async function copyFullMessage(messageId: string, text: string) {
    const ok = await writeClipboardText(text);
    if (ok) setCopiedId(messageId);
  }

  function handleMessageContextMenu(
    e: MouseEvent<HTMLDivElement>,
    messageId: string,
    fullText: string,
  ) {
    if (!shouldUseAppContextMenu()) return;
    e.preventDefault();
    setMenu({
      x: e.clientX,
      y: e.clientY,
      messageId,
      fullText,
    });
  }

  function handleDoubleClick(
    e: MouseEvent<HTMLDivElement>,
    messageId: string,
    fullText: string,
  ) {
    if (!shouldUseAppContextMenu()) return;
    e.preventDefault();
    void copyFullMessage(messageId, fullText);
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
            onContextMenu={(e) =>
              handleMessageContextMenu(e, msg.id, msg.content)
            }
            onDoubleClick={(e) => handleDoubleClick(e, msg.id, msg.content)}
          >
            <span className={styles.content} data-testid="message-content">
              {msg.content}
            </span>
            <span className={styles.time}>{msg.timestamp}</span>
            {copiedId === msg.id && (
              <span
                className={styles.copiedHint}
                data-testid="message-copied-hint"
                role="status"
              >
                ✓ Copiato
              </span>
            )}
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
              label: "📋 Copia",
              disabled: !menu.fullText.trim(),
              onSelect: () => {
                void copyFullMessage(menu.messageId, menu.fullText);
              },
            },
          ]}
        />
      )}
    </div>
  );
}
