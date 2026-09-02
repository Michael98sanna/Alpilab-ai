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
import { DiagnosticCardPanel } from "../components/diagnostic/DiagnosticCardPanel";
import { MetricsDashboard } from "../components/ai/MetricsDashboard";
import { DiagnosticPanel } from "../components/repair/DiagnosticPanel";
import { IphonePanicPanel } from "../components/repair/IphonePanicPanel";
import { RepairCardsSidebar } from "../components/repair/RepairCardsSidebar";
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
    dispatch,
    sendMessage,
    simulateVoice,
    submitMeasurement,
    loadScenario,
    pauseDiagnosis,
    resumeDiagnosis,
    toggleSessionDevices,
    nextPendingTest,
    hasActiveRepair,
    requestSnapshot,
    associateDevice,
    activateRepairDevice,
    associateManualDevice,
  } = useAppSession();

  const [section, setSection] = useState<AppSection>("chat");
  const [pairingOpen, setPairingOpen] = useState(false);
  const [addDeviceOpen, setAddDeviceOpen] = useState(false);
  const [busyProgramId, setBusyProgramId] = useState<ProgramId | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const {
    cards,
    cardMessages,
    loadingCards,
    loadCards,
    loadCardMessages,
    sendCardMessage,
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

  const isIdle =
    state.onboardingStep === "idle" &&
    state.messages.length === 0 &&
    cards.length === 0;

  const existingDeviceIds = useMemo(
    () => cards.map((card) => card.device_id),
    [cards],
  );

  useEffect(() => {
    if (cards.length === 0) {
      setActiveCardId(null);
      return;
    }
    setActiveCardId((current) => {
      if (current && cards.some((card) => card.id === current)) {
        return current;
      }
      if (state.messages.length > 0) {
        return null;
      }
      return cards[0]?.id ?? null;
    });
  }, [cards, state.messages.length]);

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

  useEffect(() => {
    if (section !== "diagnostics") {
      return;
    }
    if (mode !== "realtime" || state.connectionState !== "CONNECTED") {
      return;
    }
    if (state.tests.length > 0) {
      return;
    }
    if (!hasActiveRepair && cards.length === 0) {
      return;
    }
    requestSnapshot();
  }, [
    section,
    mode,
    state.connectionState,
    state.tests.length,
    hasActiveRepair,
    cards.length,
    requestSnapshot,
  ]);

  const handleSelectCard = useCallback(
    async (card: DiagnosticCard) => {
      setActiveCardId(card.id);
      await loadCardMessages(card.id);
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
      if (created && state.messages.length === 0) {
        setActiveCardId(created.id);
        await loadCardMessages(created.id);
      }
      setSection("chat");
      setAddDeviceOpen(false);
    },
    [sessionId, loadCards, loadCardMessages, state.messages.length],
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
            if (created && state.messages.length === 0) {
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
      state.messages.length,
    ],
  );

  const handleSendMessage = useCallback(
    async (text: string) => {
      if (activeCardId) {
        dispatch({ type: "SET_CORE_STATE", state: "THINKING" });
        try {
          await sendCardMessage(activeCardId, text);
          void loadCards();
        } finally {
          dispatch({ type: "SET_CORE_STATE", state: "IDLE" });
        }
        return;
      }
      await sendMessage(text);
      window.setTimeout(() => {
        refreshCardMessages();
        void loadCards();
      }, 600);
    },
    [activeCardId, dispatch, sendCardMessage, sendMessage, refreshCardMessages, loadCards],
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
        devices={hasActiveRepair ? state.devices : []}
        sessionDevicesExpanded={state.sessionDevicesExpanded}
        onToggleSessionDevices={toggleSessionDevices}
        onVoiceClick={simulateVoice}
        onPairDevice={showPairing ? () => setPairingOpen(true) : undefined}
        connectionState={state.connectionState}
        showConnection={mode === "realtime"}
        pcAgent={mode === "realtime" ? state.pcAgent : null}
      />

      <div className={styles.body}>
        {(section === "chat" || section === "diagnostics") && (
          <RepairCardsSidebar
            open={sidebarOpen}
            cards={cards}
            activeCardId={activeCardId}
            loading={loadingCards}
            onToggle={() => setSidebarOpen((value) => !value)}
            onSelectCard={(card) => {
              void handleSelectCard(card);
            }}
            onAddDevice={() => setAddDeviceOpen(true)}
          />
        )}

        <div className={styles.mainContent}>
          {section === "chat" && (
            <main className={styles.main} data-testid="chat-section">
              <div className={styles.chatColumn}>
                {isIdle ? (
                  <div className={styles.emptyWorkspace} data-testid="empty-workspace">
                    <h2 className={styles.emptyTitle}>Benvenuto in ALPILAB AI</h2>
                    <p className={styles.emptyHint}>
                      Inizia scrivendo in chat oppure apri le schede a sinistra e aggiungi
                      un dispositivo (USB o manuale).
                    </p>
                    {import.meta.env.DEV && mode === "mock" && (
                      <div className={styles.emptyActions}>
                        <Button variant="ghost" size="small" onClick={loadScenario}>
                          Demo scenario
                        </Button>
                      </div>
                    )}
                  </div>
                ) : (
                  <ChatTimeline
                    messages={displayMessages}
                    containerRef={containerRef}
                    onScroll={onScroll}
                    showNewMessages={showNewMessages}
                    onJumpToLatest={() => scrollToBottom("smooth")}
                  />
                )}

                <AlpilabStatusBar state={state.coreState} />
              </div>
            </main>
          )}

          {section === "diagnostics" && (
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
                variant="page"
                showHeader
              />
              <DiagnosticCardPanel
                sessionId={sessionId}
                cards={cards}
                selectedCardId={activeCardId}
                layout="page"
              />
              <MetricsDashboard />
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
      </div>

      <div className={styles.bottomChrome} data-testid="bottom-chrome">
        <MainSectionNav active={section} onChange={setSection} />
        {section === "chat" && (
          <div className={styles.inputArea}>
            <ChatInput
              onSend={(text) => {
                void handleSendMessage(text);
              }}
              onVoice={simulateVoice}
              coreState={state.coreState}
              placeholder={
                isIdle
                  ? "Cosa dobbiamo riparare?"
                  : activeCardId
                    ? "Scrivi per questo dispositivo…"
                    : cards.length > 0
                      ? "Scrivi in chat o seleziona una scheda a sinistra…"
                      : "Scrivi un messaggio…"
              }
              disabled={state.coreState === "THINKING"}
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
