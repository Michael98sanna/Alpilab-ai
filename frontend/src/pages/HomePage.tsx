import { useEffect, useState } from "react";
import { AlpilabStatusBar } from "../components/core/AlpilabStatusBar";
import { ChatInput } from "../components/chat/ChatInput";
import { ChatTimeline } from "../components/chat/ChatTimeline";
import { DiagnosticPanel } from "../components/repair/DiagnosticPanel";
import { RepairContextBanner } from "../components/repair/RepairContextBanner";
import { AppHeader } from "../components/session/AppHeader";
import { MobileContextBar } from "../components/session/MobileContextBar";
import { ContextualToolBar } from "../components/tools/ContextualToolBar";
import { BottomSheet } from "../components/ui/BottomSheet";
import { Button } from "../components/ui/Button";
import { GestureFeedback } from "../components/ui/GestureFeedback";
import { useChatScroll } from "../hooks/useChatScroll";
import { useAppSession } from "../realtime/RealtimeProvider";
import { useSwipeGesture, type PanelMode } from "../hooks/useSwipeGesture";
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
    mode,
    sendMessage,
    simulateVoice,
    submitMeasurement,
    startNewRepair,
    loadScenario,
    pauseDiagnosis,
    resumeDiagnosis,
    openDiagnostics,
    openTools,
    closeDiagnostics,
    closeTools,
    toggleSessionDevices,
    openTool,
    closeToolPanel,
    nextPendingTest,
    hasActiveRepair,
  } = useAppSession();

  const layout = useLayoutMode();
  const isMobile = layout === "mobile";
  const showContext = hasActiveRepair && state.onboardingStep === "complete";

  const panelMode: PanelMode = state.diagnosticsExpanded
    ? "diagnostics"
    : state.toolsExpanded
      ? "tools"
      : "none";

  const { containerRef, showNewMessages, scrollToBottom, onScroll } =
    useChatScroll(state.messages.length);

  const { feedback, handlers: swipeHandlers } = useSwipeGesture({
    enabled: isMobile && showContext,
    panelMode,
    onOpenDiagnostics: openDiagnostics,
    onOpenTools: openTools,
    onCloseDiagnostics: closeDiagnostics,
    onCloseTools: closeTools,
  });

  const gestureEnabled = isMobile && showContext;

  return (
    <div className={styles.layout}>
      <AppHeader
        devices={showContext ? state.devices : []}
        sessionDevicesExpanded={state.sessionDevicesExpanded}
        onToggleSessionDevices={toggleSessionDevices}
        onVoiceClick={simulateVoice}
        connectionState={state.connectionState}
        showConnection={mode === "realtime"}
        pcAgent={mode === "realtime" ? state.pcAgent : null}
      />

      {showContext && <RepairContextBanner session={state.session} />}

      <div className={styles.body}>
        <main
          className={styles.main}
          data-testid="chat-swipe-zone"
          {...(gestureEnabled ? swipeHandlers : {})}
        >
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

            {showContext && (
              <MobileContextBar
                onOpenDiagnostics={openDiagnostics}
                onOpenTools={openTools}
                diagnosticsActive={state.diagnosticsExpanded}
                toolsActive={state.toolsExpanded}
              />
            )}

            <AlpilabStatusBar state={state.coreState} />

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

        {showContext && !isMobile && state.diagnosticsExpanded && (
          <DiagnosticPanel
            tests={state.tests}
            nextTest={nextPendingTest}
            onClose={closeDiagnostics}
            onSubmitMeasurement={submitMeasurement}
            onPause={pauseDiagnosis}
            onResume={resumeDiagnosis}
            isPaused={state.session.status === "paused"}
            isSaving={state.savingTestId === nextPendingTest?.id}
            variant="side"
            showHeader
          />
        )}

        {showContext && !isMobile && state.toolsExpanded && (
          <ContextualToolBar
            tools={state.tools}
            activeToolId={state.activeToolPanel}
            onOpenTool={openTool}
            onClosePanel={closeToolPanel}
            layout="side"
          />
        )}
      </div>

      {gestureEnabled && <GestureFeedback feedback={feedback} />}

      {showContext && isMobile && state.diagnosticsExpanded && (
        <BottomSheet
          title="Diagnosi"
          onClose={closeDiagnostics}
          testId="diagnostics-sheet"
          swipeHandlers={swipeHandlers}
        >
          <DiagnosticPanel
            tests={state.tests}
            nextTest={nextPendingTest}
            onClose={closeDiagnostics}
            onSubmitMeasurement={submitMeasurement}
            onPause={pauseDiagnosis}
            onResume={resumeDiagnosis}
            isPaused={state.session.status === "paused"}
            isSaving={state.savingTestId === nextPendingTest?.id}
            variant="sheet"
          />
        </BottomSheet>
      )}

      {showContext && isMobile && state.toolsExpanded && (
        <BottomSheet
          title="Strumenti"
          onClose={closeTools}
          testId="tools-sheet"
          swipeHandlers={swipeHandlers}
        >
          <ContextualToolBar
            tools={state.tools}
            activeToolId={state.activeToolPanel}
            onOpenTool={openTool}
            onClosePanel={closeToolPanel}
            layout="sheet"
          />
        </BottomSheet>
      )}
    </div>
  );
}
