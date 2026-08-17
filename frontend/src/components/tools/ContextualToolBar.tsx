import type { ToolId, ToolItem } from "../../types";
import { Button } from "../ui/Button";
import styles from "./ContextualToolBar.module.css";

interface ContextualToolBarProps {
  tools: ToolItem[];
  expanded: boolean;
  activeToolId: ToolId | null;
  onToggle: () => void;
  onOpenTool: (id: ToolId) => void;
  onClosePanel: () => void;
  layout: "mobile" | "desktop";
}

export function ContextualToolBar({
  tools,
  expanded,
  activeToolId,
  onToggle,
  onOpenTool,
  onClosePanel,
  layout,
}: ContextualToolBarProps) {
  const activeTool = tools.find((t) => t.id === activeToolId);

  const toolButtons = tools.map((tool) => (
    <button
      key={tool.id}
      type="button"
      className={`${styles.toolBtn} ${tool.open ? styles.toolBtnActive : ""}`}
      onClick={() => onOpenTool(tool.id)}
      disabled={!tool.available}
      aria-label={tool.label}
    >
      <span>{tool.icon}</span>
      <span>{tool.label}</span>
    </button>
  ));

  return (
    <>
      {layout === "desktop" && expanded && (
        <aside className={styles.sidebar} aria-label="Strumenti contestuali">
          <button type="button" className={styles.toggle} onClick={onToggle}>
            Nascondi strumenti
          </button>
          {toolButtons}
        </aside>
      )}

      {layout === "mobile" && expanded && (
        <div className={styles.sheet} role="dialog" aria-label="Strumenti">
          {toolButtons}
          <button type="button" className={styles.toggle} onClick={onToggle}>
            Chiudi
          </button>
        </div>
      )}

      {layout === "mobile" && !expanded && (
        <div className={styles.bar}>
          <button type="button" className={styles.toggle} onClick={onToggle}>
            🛠 Strumenti
          </button>
        </div>
      )}

      {layout === "desktop" && !expanded && (
        <div className={styles.bar}>
          <button type="button" className={styles.toggle} onClick={onToggle}>
            Mostra strumenti contestuali
          </button>
        </div>
      )}

      {activeTool && (
        <div className={styles.panelOverlay} role="dialog" aria-modal="true">
          <div className={styles.panel}>
            <div className={styles.panelTitle}>
              {activeTool.icon} {activeTool.label}
            </div>
            <p className={styles.panelMock}>
              [MOCK] Workspace tecnico per {activeTool.label}. Integrazione
              hardware in fase successiva.
            </p>
            <Button onClick={onClosePanel}>Chiudi</Button>
          </div>
        </div>
      )}
    </>
  );
}
