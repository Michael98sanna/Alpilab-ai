import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type MouseEvent,
} from "react";
import type { CoreState } from "../../types";
import { readClipboardText, writeClipboardText } from "../../utils/clipboard";
import { shouldUseAppContextMenu } from "../../utils/pointerEnv";
import { ChatContextMenu } from "./ChatContextMenu";
import styles from "./ChatInput.module.css";

interface ChatInputProps {
  onSend: (text: string) => void;
  onVoice: () => void;
  coreState: CoreState;
  placeholder?: string;
  disabled?: boolean;
}

type MenuState = { x: number; y: number; hasSelection: boolean };

export function ChatInput({
  onSend,
  onVoice,
  coreState,
  placeholder = "Scrivi un messaggio...",
  disabled = false,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const [menu, setMenu] = useState<MenuState | null>(null);
  const [canPaste, setCanPaste] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const listening = coreState === "LISTENING";
  const inputDisabled = disabled || listening;

  const closeMenu = useCallback(() => setMenu(null), []);

  useEffect(() => {
    if (!menu) return;
    let cancelled = false;
    void (async () => {
      const text = await readClipboardText();
      if (!cancelled) setCanPaste(Boolean(text));
    })();
    return () => {
      cancelled = true;
    };
  }, [menu]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    // Only intercept Enter-to-send. Leave Ctrl/Cmd+C/V/X/A and Shift+Insert alone.
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  function selectionRange(): { start: number; end: number; selected: string } {
    const el = textareaRef.current;
    if (!el) return { start: 0, end: 0, selected: "" };
    const start = el.selectionStart ?? 0;
    const end = el.selectionEnd ?? 0;
    return { start, end, selected: value.slice(start, end) };
  }

  function applyText(next: string, cursor: number) {
    setValue(next);
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.focus();
      el.setSelectionRange(cursor, cursor);
    });
  }

  async function doCopy() {
    const { selected } = selectionRange();
    if (!selected) return;
    await writeClipboardText(selected);
  }

  async function doCut() {
    const { start, end, selected } = selectionRange();
    if (!selected) return;
    const ok = await writeClipboardText(selected);
    if (!ok) return;
    applyText(value.slice(0, start) + value.slice(end), start);
  }

  async function doPaste() {
    const text = await readClipboardText();
    if (text == null || text === "") return;
    const { start, end } = selectionRange();
    const next = value.slice(0, start) + text + value.slice(end);
    applyText(next, start + text.length);
  }

  function doSelectAll() {
    const el = textareaRef.current;
    if (!el) return;
    el.focus();
    el.select();
  }

  function handleContextMenu(e: MouseEvent<HTMLTextAreaElement>) {
    if (!shouldUseAppContextMenu() || inputDisabled) return;
    e.preventDefault();
    const { selected } = selectionRange();
    setMenu({
      x: e.clientX,
      y: e.clientY,
      hasSelection: selected.length > 0,
    });
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} aria-label="Input chat">
      <textarea
        ref={textareaRef}
        className={styles.input}
        rows={1}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onContextMenu={handleContextMenu}
        placeholder={placeholder}
        disabled={inputDisabled}
        aria-label="Messaggio"
        data-testid="chat-composer"
        spellCheck
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

      {menu && (
        <ChatContextMenu
          x={menu.x}
          y={menu.y}
          onClose={closeMenu}
          testId="composer-context-menu"
          items={[
            {
              id: "cut",
              label: "Taglia",
              disabled: !menu.hasSelection,
              onSelect: () => {
                void doCut();
              },
            },
            {
              id: "copy",
              label: "Copia",
              disabled: !menu.hasSelection,
              onSelect: () => {
                void doCopy();
              },
            },
            {
              id: "paste",
              label: "Incolla",
              disabled: !canPaste,
              onSelect: () => {
                void doPaste();
              },
            },
            {
              id: "select-all",
              label: "Seleziona tutto",
              disabled: value.length === 0,
              onSelect: doSelectAll,
            },
          ]}
        />
      )}
    </form>
  );
}
