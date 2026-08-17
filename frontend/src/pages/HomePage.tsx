import { useEffect, useState } from "react";
import { ChatInput } from "../components/chat/ChatInput";
import { ChatTimeline } from "../components/chat/ChatTimeline";
import { DiagnosticPanel } from "../components/repair/DiagnosticPanel";
import { RepairContextBanner } from "../components/repair/RepairContextBanner";
import { AppHeader } from "../components/session/AppHeader";
import { ContextPanel } from "../components/session/ContextPanel";
import { MobileContextBar } from "../components/session/MobileContextBar";
import { ContextualToolBar } from "../components/tools/ContextualToolBar";
import { Button } from "../components/ui/Button";
import { useChatScroll } from "../hooks/useChatScroll";
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

export function HomePage({ loadScenarioOnInit = true }: { loadScenarioOnInit?: boolean }) {
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
    toggleDiagnostics,
    toggleContextPanel,
    toggleSessionDevices,
    openTool,
    closeToolPanel,
    nextPendingTest,
    hasActiveRepair,
  } = useRepairSession(loadScenarioOnInit);

  const layout = useLayoutMode();
  const isMobile = layout === "mobile";
  const showContext = hasActiveRepair && state.onboardingStep === "complete";

  const { containerRef, showNewMessages, scrollToBottom, onScroll } =
    useChatScroll(state.messages.length);

  const openMobileDiagnostics = () => {
    if (!state.diagnosticsExpanded) toggleDiagnostics();
  };

  const openMobileTools = () => {
    if (!state.toolsExpanded) toggleTools();
  };

  return (
    <div className={styles.layout}>
      <AppHeader
        devices={showContext ? state.devices : []}
        sessionDevicesExpanded={state.sessionDevicesExpanded}
        onToggleSessionDevices={toggleSessionDevices}
        onVoiceClick={simulateVoice}
      />

      {showContext && <RepairContextBanner session={state.session} />}

      <div className={styles.body}>
        <main className={styles.main}>
          <div className={styles.chatColumn}>
            {!showContext && (
              <div className={styles.chatActions}>
                <Button variant="primary" onClick={startNewRepair}>
                  Nuova riparazione
                </Button>
                <Button variant="ghost" size="small" onClick={loadScenario}>
                  Demo scenario
                </Button>
              </div>
            )}

            <ChatTimeline
              messages={state.messages}
              containerRef={containerRef}
              onScroll={onScroll}
              showNewMessages={showNewMessages}
              onJumpToLatest={() => scrollToBottom("smooth")}
            />

            {showContext && isMobile && !state.diagnosticsExpanded && (
              <DiagnosticPanel
                tests={state.tests}
                nextTest={nextPendingTest}
                expanded={false}
                onToggle={toggleDiagnostics}
                onSubmitMeasurement={submitMeasurement}
                onPause={pauseDiagnosis}
                onResume={resumeDiagnosis}
                isPaused={state.session.status === "paused"}
              />
            )}

            {showContext && isMobile && (
              <MobileContextBar
                onOpenDiagnostics={openMobileDiagnostics}
                onOpenTools={openMobileTools}
                diagnosticsActive={state.diagnosticsExpanded}
              />
            )}

            <div className={styles.inputArea}>
              <ChatInput
                onSend={sendMessage}
                onVoice={simulateVoice}
                coreState={state.coreState}
                placeholder={
                  state.onboardingStep === "idle" && !hasActiveRepair
                    ? "Cosa dobbiamo riparare?"
                    : "Scrivi un messaggio..."
                }
                disabled={state.coreState === "THINKING"}
              />
            </div>
          </div>
        </main>

        {showContext && !isMobile && (
          <ContextPanel
            session={state.session}
            tests={state.tests}
            nextTest={nextPendingTest}
            devices={state.devices}
            tools={state.tools}
            expanded={state.contextPanelExpanded}
            diagnosticsExpanded={state.diagnosticsExpanded}
            toolsExpanded={state.toolsExpanded}
            activeToolId={state.activeToolPanel}
            onTogglePanel={toggleContextPanel}
            onToggleDiagnostics={toggleDiagnostics}
            onToggleTools={toggleTools}
            onOpenTool={openTool}
            onCloseToolPanel={closeToolPanel}
            onSubmitMeasurement={submitMeasurement}
            onPause={pauseDiagnosis}
            onResume={resumeDiagnosis}
            visible
          />
        )}
      </div>

      {showContext && isMobile && state.diagnosticsExpanded && (
        <>
          <div
            className={styles.mobileOverlay}
            onClick={toggleDiagnostics}
            aria-hidden="true"
          />
          <DiagnosticPanel
            tests={state.tests}
            nextTest={nextPendingTest}
            expanded
            onToggle={toggleDiagnostics}
            onSubmitMeasurement={submitMeasurement}
            onPause={pauseDiagnosis}
            onResume={resumeDiagnosis}
            isPaused={state.session.status === "paused"}
            variant="sheet"
          />
        </>
      )}

      {showContext && isMobile && state.toolsExpanded && (
        <ContextualToolBar
          tools={state.tools}
          expanded
          activeToolId={state.activeToolPanel}
          onToggle={toggleTools}
          onOpenTool={openTool}
          onClosePanel={closeToolPanel}
          layout="mobile"
        />
      )}
    </div>
  );
}
