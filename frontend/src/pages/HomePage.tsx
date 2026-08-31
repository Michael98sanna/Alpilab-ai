import { useCallback, useEffect, useState } from "react";
import { executeRegisteredTool } from "../api/tools";
import { AlpilabStatusBar } from "../components/core/AlpilabStatusBar";
import { ChatInput } from "../components/chat/ChatInput";
import { ChatTimeline } from "../components/chat/ChatTimeline";
import { MainSectionNav, type AppSection } from "../components/nav/MainSectionNav";
import {
  ProgramsPanel,
  type ProgramActionResult,
} from "../components/programs/ProgramsPanel";
import { DiagnosticPanel } from "../components/repair/DiagnosticPanel";
import { RepairContextBanner } from "../components/repair/RepairContextBanner";
import { DeviceSelectionPanel } from "../components/repair/DeviceSelectionPanel";
import { AppHeader } from "../components/session/AppHeader";
import { PairingDialog } from "../components/session/PairingDialog";
import { Button } from "../components/ui/Button";
import { useChatScroll } from "../hooks/useChatScroll";
import { useAppSession } from "../realtime/RealtimeProvider";
import { isPcLoopbackUi } from "../realtime/sessionStorage";
import type { LabProgram, ProgramId } from "../programs/catalog";
import { canExecuteProgram, isOpenableToolId } from "../programs/catalog";
import styles from "./HomePage.module.css";

export function HomePage() {
  const {
    state,
    mode,
    sessionId,
    sendMessage,
    simulateVoice,
    submitMeasurement,
    startNewRepair,
    loadScenario,
    pauseDiagnosis,
    resumeDiagnosis,
    toggleSessionDevices,
    nextPendingTest,
    hasActiveRepair,
    associateDevice,
    unassociateDevice,
  } = useAppSession();

  const repairContextReady = Boolean(state.session.device && state.session.issue);
  const showContext =
    hasActiveRepair &&
    (state.onboardingStep === "complete" || repairContextReady);

  const { containerRef, showNewMessages, scrollToBottom, onScroll } =
    useChatScroll(state.messages.length);

  const [section, setSection] = useState<AppSection>("chat");
  const [pairingOpen, setPairingOpen] = useState(false);
  const [devicePanelDismissed, setDevicePanelDismissed] = useState(false);
  const [busyProgramId, setBusyProgramId] = useState<ProgramId | null>(null);
  const showPairing = isPcLoopbackUi();

  const showDevicePanel =
    !devicePanelDismissed &&
    (state.detectedDevices.length > 0 || state.deviceContext !== null);

  useEffect(() => {
    if (state.detectedDevices.length > 0) {
      setDevicePanelDismissed(false);
    }
  }, [state.detectedDevices.length]);

  useEffect(() => {
    if (section === "diagnostics" && !hasActiveRepair) {
      setSection("chat");
    }
  }, [section, hasActiveRepair]);

  const handleOpenProgram = useCallback(
    async (program: LabProgram): Promise<ProgramActionResult> => {
      if (!canExecuteProgram(program) || !isOpenableToolId(program.toolId)) {
        return { ok: false, message: "Non ancora configurato" };
      }
      const toolId = program.toolId;

      if (mode !== "realtime") {
        return {
          ok: false,
          message: "Disponibile solo in modalità realtime con PC Agent.",
        };
      }

      const agentId = state.pcAgent?.agentId;
      if (!agentId || !state.pcAgent?.online) {
        return { ok: false, message: "PC Agent non disponibile." };
      }

      setBusyProgramId(program.id);
      try {
        const result = await executeRegisteredTool(sessionId, agentId, toolId);
        if (result.success) {
          if (result.result.already_running === true) {
            return { ok: true, message: `✓ ${program.name} già aperto` };
          }
          return { ok: true, message: `✓ ${program.name} avviato` };

          if (result.result.already_running === true) {
            return {
              ok: true,
              message:
                toolId === "windows.alpilab_check.open"
                  ? "✓ Alpilab Check già aperto"
                  : "✓ 3uTools già aperto",
            };
          }
          return {
            ok: true,
            message:
              toolId === "windows.alpilab_check.open"
                ? "✓ Alpilab Check avviato"
                : "✓ 3uTools avviato",
          };
        }
        const err = result.error || "";
        const label =
          toolId === "windows.alpilab_check.open" ? "Alpilab Check" : "3uTools";
        if (err === "APP_NOT_REGISTERED" || err === "TOOL_DISABLED") {
          return { ok: false, message: "Non ancora configurato" };
        }
        if (err === "EXECUTABLE_NOT_FOUND") {
          return {
            ok: false,
            message: `✕ Impossibile aprire ${label} — eseguibile non trovato`,
          };
        }
        return {
          ok: false,
          message: err
            ? `✕ Impossibile aprire ${label}: ${err}`
            : `✕ Impossibile aprire ${label}`,
        };
      } catch {
        return { ok: false, message: "Errore di rete durante l'apertura." };
      } finally {
        setBusyProgramId(null);
      }
    },
    [mode, sessionId, state.pcAgent],
  );

  return (
    <div className={styles.layout}>
      <AppHeader
        devices={showContext ? state.devices : []}
        sessionDevicesExpanded={state.sessionDevicesExpanded}
        onToggleSessionDevices={toggleSessionDevices}
        onVoiceClick={simulateVoice}
        onPairDevice={showPairing ? () => setPairingOpen(true) : undefined}
        connectionState={state.connectionState}
        showConnection={mode === "realtime"}
        pcAgent={mode === "realtime" ? state.pcAgent : null}
      />

      {showContext && <RepairContextBanner session={state.session} />}

      {showDevicePanel && (
        <DeviceSelectionPanel
          detectedDevices={state.detectedDevices}
          deviceContext={state.deviceContext}
          onAssociate={associateDevice}
          onUnassociate={unassociateDevice}
          onDismiss={() => setDevicePanelDismissed(true)}
        />
      )}

      <div className={styles.body}>
        {section === "chat" && (
          <main className={styles.main} data-testid="chat-section">
            <div className={styles.chatColumn}>
              {!showContext && (
                <div className={styles.chatActions}>
                  <Button variant="primary" onClick={startNewRepair}>
                    Nuova riparazione
                  </Button>
                  {mode !== "realtime" && (
                    <Button variant="ghost" size="small" onClick={loadScenario}>
                      Demo scenario
                    </Button>
                  )}
                </div>
              )}

              <ChatTimeline
                messages={state.messages}
                containerRef={containerRef}
                onScroll={onScroll}
                showNewMessages={showNewMessages}
                onJumpToLatest={() => scrollToBottom("smooth")}
              />

              <AlpilabStatusBar state={state.coreState} />
            </div>
          </main>
        )}

        {section === "diagnostics" && hasActiveRepair && (
          <main className={styles.main} data-testid="diagnostics-section">
            <DiagnosticPanel
              tests={state.tests}
              nextTest={nextPendingTest}
              onSubmitMeasurement={submitMeasurement}
              onPause={pauseDiagnosis}
              onResume={resumeDiagnosis}
              isPaused={state.session.status === "paused"}
              isSaving={state.savingTestId === nextPendingTest?.id}
              variant="sheet"
              showHeader
            />
          </main>
        )}

        {section === "programs" && (
          <main className={styles.main} data-testid="programs-section">
            <ProgramsPanel
              onOpenProgram={handleOpenProgram}
              busyProgramId={busyProgramId}
            />
          </main>
        )}
      </div>

      <div className={styles.bottomChrome} data-testid="bottom-chrome">
        <MainSectionNav
          active={section}
          onChange={setSection}
          diagnosticsEnabled={hasActiveRepair}
        />
        {section === "chat" && (
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
        )}
      </div>

      {pairingOpen && <PairingDialog onClose={() => setPairingOpen(false)} />}
    </div>
  );
}
