import { useEffect, useState } from "react";
import { AlpilabCore } from "../components/core/AlpilabCore";
import { ChatInput } from "../components/chat/ChatInput";
import { MessageList } from "../components/chat/MessageList";
import { DiagnosticPanel } from "../components/repair/DiagnosticPanel";
import { RepairBanner } from "../components/repair/RepairBanner";
import { AppHeader } from "../components/session/AppHeader";
import { SessionDevices } from "../components/session/SessionDevices";
import { ContextualToolBar } from "../components/tools/ContextualToolBar";
import { Button } from "../components/ui/Button";
import { useRepairSession } from "../hooks/useRepairSession";
import styles from "./HomePage.module.css";

function useLayoutMode() {
  const [mode, setMode] = useState<"mobile" | "desktop">("desktop");

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1024px)");
    const update = () => setMode(mq.matches ? "desktop" : "mobile");
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  return mode;
}

export function HomePage() {
  const {
    state,
    sendMessage,
    simulateVoice,
    submitMeasurement,
    startNewRepair,
    loadScenario,
    pauseDiagnosis,
    resumeDiagnosis,
    toggleTools,
    openTool,
    closeToolPanel,
    nextPendingTest,
    hasActiveRepair,
  } = useRepairSession(true);

  const layout = useLayoutMode();
  const showDiagnostics =
    hasActiveRepair && state.onboardingStep === "complete";

  const heroText =
    state.onboardingStep === "idle" && !hasActiveRepair
      ? "Cosa dobbiamo riparare?"
      : state.onboardingStep === "device"
        ? "Che dispositivo dobbiamo riparare?"
        : state.onboardingStep === "issue"
          ? "Qual è il problema?"
          : null;

  return (
    <div className={styles.layout}>
      <AppHeader onVoiceClick={simulateVoice} />

      <div className={styles.body}>
        <main className={styles.main}>
          <div className={styles.chatColumn}>
            <AlpilabCore state={state.coreState} />

            {heroText && <p className={styles.hero}>{heroText}</p>}

            <div className={styles.actions}>
              <Button variant="primary" onClick={startNewRepair}>
                Nuova riparazione
              </Button>
              <Button variant="ghost" size="small" onClick={loadScenario}>
                Demo scenario
              </Button>
            </div>

            <MessageList messages={state.messages} coreState={state.coreState} />

            <ChatInput
              onSend={sendMessage}
              onVoice={simulateVoice}
              coreState={state.coreState}
              placeholder="Scrivi un messaggio..."
              disabled={state.coreState === "THINKING"}
            />
          </div>
        </main>

        {showDiagnostics && (
          <aside className={styles.sideColumn} aria-label="Contesto riparazione">
            <SessionDevices devices={state.devices} visible={hasActiveRepair} />
            <RepairBanner session={state.session} />
            <DiagnosticPanel
              tests={state.tests}
              nextTest={nextPendingTest}
              onSubmitMeasurement={submitMeasurement}
              onPause={pauseDiagnosis}
              onResume={resumeDiagnosis}
              isPaused={state.session.status === "paused"}
            />
          </aside>
        )}
      </div>

      {showDiagnostics && (
        <ContextualToolBar
          tools={state.tools}
          expanded={state.toolsExpanded}
          activeToolId={state.activeToolPanel}
          onToggle={toggleTools}
          onOpenTool={openTool}
          onClosePanel={closeToolPanel}
          layout={layout}
        />
      )}
    </div>
  );
}
