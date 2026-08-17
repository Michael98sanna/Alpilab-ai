import type { DiagnosticTest, RepairSession, SessionDevice, ToolId, ToolItem } from "../../types";
import { DiagnosticPanel } from "../repair/DiagnosticPanel";
import { ContextualToolBar } from "../tools/ContextualToolBar";
import styles from "./ContextPanel.module.css";

interface ContextPanelProps {
  session: RepairSession;
  tests: DiagnosticTest[];
  nextTest?: DiagnosticTest;
  devices: SessionDevice[];
  tools: ToolItem[];
  expanded: boolean;
  diagnosticsExpanded: boolean;
  toolsExpanded: boolean;
  activeToolId: ToolId | null;
  onTogglePanel: () => void;
  onToggleDiagnostics: () => void;
  onToggleTools: () => void;
  onOpenTool: (id: ToolId) => void;
  onCloseToolPanel: () => void;
  onSubmitMeasurement: (testId: string, value: string) => void;
  onPause: () => void;
  onResume: () => void;
  visible: boolean;
}

/** Legacy desktop context rail — superseded by on-demand side panels in V0.3. */
export function ContextPanel({
  session,
  tests,
  nextTest,
  tools,
  expanded,
  diagnosticsExpanded,
  toolsExpanded,
  activeToolId,
  onTogglePanel,
  onToggleDiagnostics,
  onToggleTools,
  onOpenTool,
  onCloseToolPanel,
  onSubmitMeasurement,
  onPause,
  onResume,
  visible,
}: ContextPanelProps) {
  if (!visible) return null;

  if (!expanded) {
    return (
      <aside className={styles.collapsedRail} aria-label="Pannello contesto">
        <button type="button" className={styles.expandBtn} onClick={onTogglePanel}>
          ◀ Contesto
        </button>
      </aside>
    );
  }

  return (
    <aside className={styles.panel} aria-label="Pannello contesto">
      <div className={styles.panelHeader}>
        <span>Contesto</span>
        <button type="button" className={styles.collapseBtn} onClick={onTogglePanel}>
          Chiudi ▸
        </button>
      </div>

      {diagnosticsExpanded && (
        <DiagnosticPanel
          tests={tests}
          nextTest={nextTest}
          onClose={onToggleDiagnostics}
          onSubmitMeasurement={onSubmitMeasurement}
          onPause={onPause}
          onResume={onResume}
          isPaused={session.status === "paused"}
          variant="side"
          showHeader
        />
      )}

      {toolsExpanded && (
        <div className={styles.toolsSection}>
          <ContextualToolBar
            tools={tools}
            activeToolId={activeToolId}
            onOpenTool={onOpenTool}
            onClosePanel={onCloseToolPanel}
            layout="side"
          />
        </div>
      )}

      {!diagnosticsExpanded && !toolsExpanded && (
        <div className={styles.toolsSection}>
          <button type="button" className={styles.expandBtn} onClick={onToggleDiagnostics}>
            Apri diagnosi
          </button>
          <button type="button" className={styles.expandBtn} onClick={onToggleTools}>
            Apri strumenti
          </button>
        </div>
      )}
    </aside>
  );
}
