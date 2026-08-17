import type { ChatMessage, CoreState } from "../../types";
import styles from "./ChatPanel.module.css";

interface MessageListProps {
  messages: ChatMessage[];
  coreState: CoreState;
}

export function MessageList({ messages, coreState }: MessageListProps) {
  return (
    <div className={styles.list} role="log" aria-label="Conversazione">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`${styles.message} ${styles[msg.role]}`}
        >
          {msg.content}
          <span className={styles.time}>{msg.timestamp}</span>
        </div>
      ))}
      {coreState === "THINKING" && (
        <div className={styles.thinking} aria-label="AI sta elaborando">
          <span>Alpilab sta pensando</span>
          <span className={styles.dots}>
            <span>.</span><span>.</span><span>.</span>
          </span>
        </div>
      )}
    </div>
  );
}
