import type { ToolId, ToolItem } from "../../types";
import { Button } from "../ui/Button";
import styles from "./ContextualToolBar.module.css";

interface ContextualToolBarProps {
  tools: ToolItem[];
  activeToolId: ToolId | null;
  onOpenTool: (id: ToolId) => void;
  onClosePanel: () => void;
  layout: "sheet" | "side";
}

export function ContextualToolBar({
  tools,
  activeToolId,
  onOpenTool,
  onClosePanel,
  layout,
}: ContextualToolBarProps) {
  const activeTool = tools.find((t) => t.id === activeToolId);

  const toolList = (
    <div className={layout === "sheet" ? styles.toolList : styles.sidebarList}>
      {tools.map((tool) => (
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
      ))}
    </div>
  );

  return (
    <>
      {layout === "sheet" ? (
        <div data-testid="tools-sheet-content">{toolList}</div>
      ) : (
        <aside className={styles.sidePanel} aria-label="Strumenti" data-testid="tools-side-panel">
          {toolList}
        </aside>
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
