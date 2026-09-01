import { useCallback, useEffect, useMemo, useState } from "react";
import { executeRegisteredTool } from "../api/tools";
import { createDiagnosticCard } from "../api/diagnosticCards";
import type { DiagnosticCard } from "../api/diagnosticCards";
import { AlpilabStatusBar } from "../components/core/AlpilabStatusBar";
import { ChatInput } from "../components/chat/ChatInput";
import { ChatTimeline } from "../components/chat/ChatTimeline";
import { MainSectionNav, type AppSection } from "../components/nav/MainSectionNav";
import {
  ProgramsPanel,
  type ProgramActionResult,
} from "../components/programs/ProgramsPanel";
import { AddDeviceDialog } from "../components/repair/AddDeviceDialog";
import { DiagnosticPanel } from "../components/repair/DiagnosticPanel";
import { IphonePanicPanel } from "../components/repair/IphonePanicPanel";
import { RepairCardsSidebar } from "../components/repair/RepairCardsSidebar";
import { RepairContextBanner } from "../components/repair/RepairContextBanner";
import { DeviceSelectionPanel } from "../components/repair/DeviceSelectionPanel";
import { AppHeader } from "../components/session/AppHeader";
import { PairingDialog } from "../components/session/PairingDialog";
import { Button } from "../components/ui/Button";
import { useChatScroll } from "../hooks/useChatScroll";
import { useRepairCards } from "../hooks/useRepairCards";
import { useAppSession } from "../realtime/RealtimeProvider";
import { isPcLoopbackUi } from "../realtime/sessionStorage";
import type { LabProgram, ProgramId } from "../programs/catalog";
import { canExecuteProgram, isOpenableToolId } from "../programs/catalog";
import styles from "./HomePage.module.css";
import { deviceDisplayName, hasIphoneConnected } from "../utils/deviceKind";

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
    activateRepairDevice,
    associateManualDevice,
  } = useAppSession();

  const repairContextReady = Boolean(state.session.device && state.session.issue);
  const showContext =
    hasActiveRepair &&
    (state.onboardingStep === "complete" || repairContextReady);

  const [section, setSection] = useState<AppSection>("chat");
  const [pairingOpen, setPairingOpen] = useState(false);
  const [addDeviceOpen, setAddDeviceOpen] = useState(false);
  const [devicePanelDismissed, setDevicePanelDismissed] = useState(false);
  const [busyProgramId, setBusyProgramId] = useState<ProgramId | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);

  const {
    cards,
    cardMessages,
    loadingCards,
    loadCards,
    loadCardMessages,
    refreshCardMessages,
  } = useRepairCards(sessionId, activeCardId);

  const displayMessages = activeCardId ? cardMessages : state.messages;

  const { containerRef, showNewMessages, scrollToBottom, onScroll } =
    useChatScroll(displayMessages.length);

  const showPairing = isPcLoopbackUi();
  const iphoneConnected = hasIphoneConnected(
    state.deviceContext,
    state.detectedDevices,
  );

  const showDevicePanel =
    !hasActiveRepair &&
    !devicePanelDismissed &&
    (state.detectedDevices.length > 0 || state.deviceContext !== null);

  const existingDeviceIds = useMemo(
    () => cards.map((card) => card.device_id),
    [cards],
  );

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

  useEffect(() => {
    if (!hasActiveRepair) {
      setActiveCardId(null);
      return;
    }
    if (cards.length === 0) {
      setActiveCardId(null);
      return;
    }
    setActiveCardId((current) => {
      if (current && cards.some((card) => card.id === current)) {
        return current;
      }
      return cards[0]?.id ?? null;
    });
  }, [hasActiveRepair, cards]);

  useEffect(() => {
    if (!activeCardId) {
      return;
    }
    const activeCard = cards.find((card) => card.id === activeCardId);
    if (!activeCard) {
      return;
    }
    activateRepairDevice({
      repair_device_id: activeCard.device_id,
      device_name: activeCard.device_name,
    });
  }, [activeCardId, cards, activateRepairDevice]);

  const handleSelectCard = useCallback(
    async (card: DiagnosticCard) => {
      setActiveCardId(card.id);
      await loadCardMessages(card.id);
      setSection("chat");
    },
    [loadCardMessages],
  );

  const ensureCardForDevice = useCallback(
    async (deviceId: string, deviceName: string) => {
      await createDiagnosticCard({
        session_id: sessionId,
        device_id: deviceId,
        device_name: deviceName,
      }).catch(() => {
        /* idempotent */
      });
      const nextCards = await loadCards();
      const created = nextCards.find((card) => card.device_id === deviceId);
      if (created) {
        setActiveCardId(created.id);
        await loadCardMessages(created.id);
      }
      setSection("chat");
      setAddDeviceOpen(false);
    },
    [sessionId, loadCards, loadCardMessages],
  );

  const handleAssociateDetected = useCallback(
    async (deviceId: string) => {
      const detected = state.detectedDevices.find((device) => device.id === deviceId);
      if (!detected) {
        return;
      }
      associateDevice(deviceId);
      await ensureCardForDevice(
        deviceId,
        deviceDisplayName(detected.brand, detected.model, detected.id),
      );
    },
    [associateDevice, ensureCardForDevice, state.detectedDevices],
  );

  const handleAddManualDevice = useCallback(
    async (brand: string, model: string) => {
      const previousIds = new Set(cards.map((card) => card.id));
      if (mode === "realtime") {
        associateManualDevice(brand, model);
        window.setTimeout(() => {
          void loadCards().then((nextCards) => {
            const created =
              nextCards.find((card) => !previousIds.has(card.id)) ??
              nextCards.find((card) => card.device_id.startsWith("manual-"));
            if (created) {
              void handleSelectCard(created);
            }
          });
        }, 500);
        setAddDeviceOpen(false);
        return;
      }
      const deviceId = associateManualDevice(brand, model);
      await ensureCardForDevice(
        deviceId,
        deviceDisplayName(brand, model, deviceId),
      );
    },
    [
      associateManualDevice,
      cards,
      ensureCardForDevice,
      handleSelectCard,
      loadCards,
      mode,
    ],
  );

  const handleSendMessage = useCallback(
    async (text: string) => {
      await sendMessage(text);
      window.setTimeout(() => {
        refreshCardMessages();
        void loadCards();
      }, 600);
    },
    [sendMessage, refreshCardMessages, loadCards],
  );

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
        }
        const err = result.error || "";
        const label = program.name;
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
            <div className={styles.chatLayout}>
              {hasActiveRepair && (
                <RepairCardsSidebar
                  cards={cards}
                  activeCardId={activeCardId}
                  loading={loadingCards}
                  onSelectCard={(card) => {
                    void handleSelectCard(card);
                  }}
                  onAddDevice={() => setAddDeviceOpen(true)}
                />
              )}

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
                  messages={displayMessages}
                  containerRef={containerRef}
                  onScroll={onScroll}
                  showNewMessages={showNewMessages}
                  onJumpToLatest={() => scrollToBottom("smooth")}
                />

                <AlpilabStatusBar state={state.coreState} />
              </div>
            </div>
          </main>
        )}

        {section === "diagnostics" && hasActiveRepair && (
          <main className={styles.diagnosticsMain} data-testid="diagnostics-section">
            {iphoneConnected && <IphonePanicPanel />}
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
              onSend={(text) => {
                void handleSendMessage(text);
              }}
              onVoice={simulateVoice}
              coreState={state.coreState}
              placeholder={
                !hasActiveRepair
                  ? "Cosa dobbiamo riparare?"
                  : activeCardId
                    ? "Scrivi per questo dispositivo..."
                    : "Aggiungi un dispositivo per iniziare..."
              }
              disabled={
                state.coreState === "THINKING" || (hasActiveRepair && !activeCardId)
              }
            />
          </div>
        )}
      </div>

      {pairingOpen && <PairingDialog onClose={() => setPairingOpen(false)} />}
      {addDeviceOpen && (
        <AddDeviceDialog
          detectedDevices={state.detectedDevices}
          existingDeviceIds={existingDeviceIds}
          onAssociateDetected={(deviceId) => {
            void handleAssociateDetected(deviceId);
          }}
          onAddManual={(brand, model) => {
            void handleAddManualDevice(brand, model);
          }}
          onClose={() => setAddDeviceOpen(false)}
        />
      )}
    </div>
  );
}
