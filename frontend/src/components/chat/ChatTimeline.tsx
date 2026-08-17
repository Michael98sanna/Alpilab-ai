import type { RefObject } from "react";
import type { ChatMessage } from "../../types";
import styles from "./ChatPanel.module.css";

interface ChatTimelineProps {
  messages: ChatMessage[];
  containerRef: RefObject<HTMLDivElement>;
  onScroll: () => void;
  showNewMessages: boolean;
  onJumpToLatest: () => void;
}

export function ChatTimeline({
  messages,
  containerRef,
  onScroll,
  showNewMessages,
  onJumpToLatest,
}: ChatTimelineProps) {
  const chatMessages = messages.filter((m) => m.role !== "status");

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
          >
            {msg.content}
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
    </div>
  );
}
