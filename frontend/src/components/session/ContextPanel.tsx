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

      <DiagnosticPanel
        tests={tests}
        nextTest={nextTest}
        expanded={diagnosticsExpanded}
        onToggle={onToggleDiagnostics}
        onSubmitMeasurement={onSubmitMeasurement}
        onPause={onPause}
        onResume={onResume}
        isPaused={session.status === "paused"}
      />

      <div className={styles.toolsSection}>
        <ContextualToolBar
          tools={tools}
          expanded={toolsExpanded}
          activeToolId={activeToolId}
          onToggle={onToggleTools}
          onOpenTool={onOpenTool}
          onClosePanel={onCloseToolPanel}
          layout="desktop"
        />
      </div>
    </aside>
  );
}
