import { useState, type FormEvent, type KeyboardEvent } from "react";
import type { CoreState } from "../../types";
import styles from "./ChatInput.module.css";

interface ChatInputProps {
  onSend: (text: string) => void;
  onVoice: () => void;
  coreState: CoreState;
  placeholder?: string;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  onVoice,
  coreState,
  placeholder = "Scrivi un messaggio...",
  disabled = false,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const listening = coreState === "LISTENING";

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} aria-label="Input chat">
      <textarea
        className={styles.input}
        rows={1}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || listening}
        aria-label="Messaggio"
      />
      <button
        type="button"
        className={`${styles.mic} ${listening ? styles.micActive : ""}`}
        aria-label="Microfono"
        aria-pressed={listening}
        onClick={onVoice}
        disabled={disabled}
      >
        🎙️
      </button>
      <button
        type="submit"
        className={styles.send}
        aria-label="Invia messaggio"
        disabled={disabled || !value.trim()}
      >
        ↑
      </button>
    </form>
  );
}
