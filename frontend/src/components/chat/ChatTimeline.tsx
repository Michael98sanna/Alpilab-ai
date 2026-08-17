import type { RefObject } from "react";
import type { ChatMessage } from "../../types";
import { AssistantStatusMessage } from "./AssistantStatusMessage";
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
        {messages.map((msg) =>
          msg.role === "status" && msg.coreState ? (
            <AssistantStatusMessage
              key={msg.id}
              state={msg.coreState}
              label={msg.content}
              timestamp={msg.timestamp}
            />
          ) : (
            <div
              key={msg.id}
              className={`${styles.message} ${styles[msg.role]}`}
              data-testid={`message-${msg.role}`}
            >
              {msg.content}
              <span className={styles.time}>{msg.timestamp}</span>
            </div>
          ),
        )}
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
