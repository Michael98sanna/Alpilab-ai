# Architettura Alpilab AI (V2)

Questo documento descrive l'architettura prevista di Alpilab AI e lo stato attuale del software foundation.

Alpilab AI è un **ambiente di lavoro condiviso** per il laboratorio, non una semplice chat AI. L'entità centrale è la **Repair Session**, indipendente dal dispositivo client.

---

## 1. System architecture

```text
                    ALPILAB AI CLOUD
                           |
        +------------------+------------------+
        |                  |                  |
   AI Router      Conversation/Command    Session Store
        |                  Engine                  |
        +------------------+----------------------+
                           |
              RealtimeSessionManager
                           |
                    Web / PWA (future)
                           |
              +------------+------------+
              |            |            |
             PC       Smartphone     Tablet
                           |
                    ALPILAB HUB (future)
                           |
        +------------------+------------------+
        |                  |                  |
   Alpilab Check      Software           Hardware
                     3uTools            Microscopio
                     Borneo             Termocamera
                     ZXW                 Multimetro
                                         Alimentatore
```

**Principi:**

- Cloud-first, responsive web + futura PWA (no app native separate in questa fase)
- Provider AI intercambiabili (`AIProvider` + `AIRouter`)
- Separazione netta da Alpilab Check (solo `AlpilabCheckConnector`)
- Hub Windows separato (`AlpilabHub`) — mock in questa fase
- Nessuna esecuzione shell arbitraria

---

## 2. Repair Session

La sessione appartiene alla **riparazione**, non al dispositivo.

```text
Repair Session
    |
    +-- PC / Smartphone / Tablet (SessionParticipant)
    +-- PC Agent (technical participant — V0.1)
    |
    +-- Chat (ConversationMessage)
    +-- Voice (stesso engine, post-STT)
    +-- Measurements
    +-- Images
    +-- Diagnostics (DiagnosticStateManager)
    +-- AI context
    +-- Tool state (ToolRegistry)
```

**Modelli:**

| Modello | File | Ruolo |
|---------|------|--------|
| `RepairSession` | `app/schemas/repair.py` | Entità riparazione (contratto dati) |
| `RepairSessionContext` | `app/schemas/session.py` | Stato runtime multi-device, mode, flow |
| `SessionParticipant` | `app/schemas/session.py` | Collegamento device ↔ sessione |
| `User`, `ClientDevice` | `app/schemas/session.py` | Utente e client connessi |

---

## 3. Multi-device synchronization

- Un utente può avere più `ClientDevice` (PC, Android, iOS, tablet)
- Più partecipanti possono aprire la **stessa** `RepairSession`
- Il cambio dispositivo **non** crea una nuova sessione
- `SessionResumeManager` + `InMemorySessionStore` (mock persistence)
- Resume automatico se una sola sessione attiva rilevante; altrimenti lista recenti

---

## 4. Realtime events (V1 + V1.1)

**Layer:** `app/realtime/` + `app/main.py` (FastAPI)

### Chat realtime ≠ Session realtime

| V1 | V1.1 |
|----|------|
| Chat sincronizzata tra dispositivi | **Intera RepairSession** sincronizzata |
| Snapshot solo per onboarding UI | Snapshot = stato completo + `state_version` |
| Diagnostica locale per device | Server valida e broadcasta ogni modifica |

### Flusso condiviso (source of truth)

```text
DEVICE A
    ↓  action (diagnostic_update, diagnosis_pause, …)
WebSocket
    ↓
FastAPI
    ↓
RealtimeSessionManager / RepairSession (in-memory)
    ↓  state_version++
SESSION_STATE_UPDATED (+ optional legacy events)
    ↓  broadcast
┌─────────┬─────────┬─────────┐
DEVICE A  DEVICE B  DEVICE C
```

Il client **non** fa broadcast peer-to-peer: notifica il server, il server muta lo stato e trasmette.

### Eventi principali

| Evento | Ruolo |
|--------|--------|
| `SESSION_SNAPSHOT` | Stato completo su connect / reconnect / `request_snapshot` |
| `SESSION_STATE_UPDATED` | Delta incrementale con `state_version` + `changes` |
| `STATE_UPDATE_REJECTED` | Modifica rifiutata (validazione, pausa, test sconosciuto) |
| `CHAT_MESSAGE` | Messaggi conversazione |
| `ASSISTANT_STATUS` | Legacy compat; anche in `SESSION_STATE_UPDATED.changes` |
| `DIAGNOSTIC_UPDATED` | Lista completa diagnostica (legacy compat) |
| `DEVICE_CONNECTED` / `DEVICE_DISCONNECTED` | Presence multi-device |

### state_version e conflitti

- Ogni mutazione server-side incrementa `state_version` (1, 2, 3, …)
- Il server serializza le richieste concorrenti (last-write-wins per campo)
- Se un client riceve versione `N+2` senza `N+1`, invia `request_snapshot` (no inventing state)
- Duplicati (`version <= locale`) vengono ignorati

### Inbound WebSocket (client → server)

`chat_message`, `heartbeat`, `assistant_status`, `diagnostic_update`, `diagnosis_pause`, `repair_context_update`, `request_snapshot`

**Authentication and authorization will be implemented before production deployment.**

`RealtimeSessionManager` gestisce sessioni in-memory, presence dispositivi, broadcast eventi e snapshot iniziale per nuovi partecipanti.

**Frontend realtime:** `frontend/src/realtime/` — `RealtimeClient`, `RealtimeProvider`, `applyStateChanges`, modalità `MOCK` | `REALTIME`.

---

## 4.1 PC Agent (V0.1 + V0.2)

The PC Agent is a **local Windows process** that joins a RepairSession as a technical participant. It is not a separate session.

```text
                    ALPILAB AI
                         │
                  RepairSession
                         │
              ToolExecutionService
                         │
                  Authorization
                         │
                   ToolRegistry
                         │
                   AgentGateway
                         │
              WebSocket /ws/agent/{session_id}
                         │
                         ▼
                  ALPILAB PC AGENT
                         │
                LocalToolDispatcher
                         │
              demo.safe_test (V0.2)
```

### Components

| Component | Location | Role |
|-----------|----------|------|
| `AgentRegistry` | `app/agent/registry.py` | In-memory runtime registry (register, heartbeat, list) |
| `AgentGateway` | `app/agent/gateway.py` | Registration, heartbeat, command routing, session broadcast |
| `ToolExecutionService` | `app/agent/tool_executor.py` | Auth + registry + dispatch + timeout + idempotency |
| `ToolExecutionStore` | `app/agent/execution_store.py` | Pending/completed executions by `request_id` |
| `authorize_tool_execution` | `app/security/tool_authorization.py` | Risk level + capability checks |
| `ExecutableToolSpec` | `app/tools/executable.py` | Server-controlled tool definitions |
| Agent WebSocket | `app/agent/ws.py` | `/ws/agent/{session_id}` endpoint |
| PC Agent process | `pc_agent/` | Local client + `LocalToolDispatcher` |
| Session state | `RealtimeSessionData.pc_agent` | Agent presence on shared session |

### Connection states

`OFFLINE` → `CONNECTING` → `CONNECTED` → `REGISTERING` → `ONLINE`  
On disconnect: `RECONNECTING` with exponential backoff.

### Realtime events

| Event | Role |
|-------|------|
| `AGENT_CONNECTED` | Agent registered; smartphone/tablet see PC Agent online |
| `AGENT_DISCONNECTED` | Agent offline |
| `AGENT_HEARTBEAT` | Liveness refresh |
| `AGENT_TEST_RESULT` | Response to server-initiated test command |
| `TOOL_EXECUTION_STARTED` | Authorized tool dispatch to agent (V0.2) |
| `TOOL_EXECUTION_COMPLETED` | Agent result received (V0.2) |
| `TOOL_EXECUTE_RESULT` | Result broadcast to RepairSession clients (V0.2) |

### Security (V0.2)

- WebSocket is **not** a secure command channel for arbitrary execution
- Agent allowlist accepts **only** `AGENT_TEST` and `TOOL_EXECUTE`
- Server `ToolRegistry` is the source of truth — clients cannot define tools
- `LocalToolDispatcher` executes only pre-registered handlers — no shell/subprocess
- `ActionRiskLevel` SAFE/READ_ONLY auto-execute; higher levels rejected until confirmation flow exists
- Idempotency via `request_id`; execution timeout (default 30s)

Full details: [PC_AGENT.md](PC_AGENT.md)

---

## 5. Conversation vs Command

**Separazione esplicita:**

| Flusso | Engine | Esempio |
|--------|--------|---------|
| Conversazione | `ConversationCommandEngine` → `AIRouter` | "Cosa può causare un boot loop?" |
| Comando | `ConversationCommandEngine` → `CommandEngine` | "Apri termocamera" |

Modelli: `Intent`, `Command`, `Action`, `ActionResult` in `app/schemas/commands.py`

Parser foundation: `MockCommandParser` (rule-based, non NLP production).

---

## 6. Voice/Text parity

Voce e testo condividono **un solo** `ConversationCommandEngine`:

```text
TEXT ──► Parser ──► Conversation / Command
                         ▲
VOICE ──► Mock STT ──────┘
```

Interfacce mock: `SpeechToText`, `TextToSpeech`, `VoiceInput` in `app/voice/`.

La trascrizione vocale diventa un `ConversationMessage` con `channel=voice`.

---

## 7. Diagnostic state machine

**Layer:** `app/diagnostics/`

`DiagnosticStateManager` gestisce test fuori dai prompt AI.

Stati (`DiagnosticTestStatus`):

`PENDING` → `IN_PROGRESS` → `PASSED` / `FAILED` / `SKIPPED` / `INVALID`

Evidenze (`RecordedEvidence`): valore, unità, fonte, strumento, timestamp, note, confidence.

Tipi evidenza (`EvidenceKind`): `observation`, `measurement`, `hypothesis`, `diagnosis`.

---

## 8. Anti-loop strategy

Requisito critico: **non riproporre test già validati**.

Implementazione (non solo prompt):

- `should_recommend_test()` — blocca re-proposta se test PASSED/FAILED con evidenza
- `RepeatedRecommendationDetector` — max ripetizioni nella finestra temporale
- `max_retries` per test INVALID
- `SessionEvent` log per audit

---

## 9. Guided/Free mode

`SessionMode`: `GUIDED` | `FREE` — in `RepairSessionContext`.

`SessionFlowState`: `ACTIVE`, `PAUSED`, `STOPPED`, `RESUMED`.

L'utente può passare da guided a free in qualsiasi momento. La diagnosi guidata non è un wizard rigido.

Comandi: `STOP`, `PAUSE`, `RESUME`, `RESET_DIAGNOSTIC_FLOW`, `CONTINUE_DIAGNOSIS`.

---

## 10. Tool architecture

**Layer:** `app/tools/` + `pc_agent/tools/`

`Tool` generico: id, name, type, status, capabilities (UI/inventory mock).

**Executable tools (V0.2):** `ExecutableToolSpec` — server-controlled registration with `tool_id`, `risk_level`, `required_capabilities`, `allowed_argument_keys`.

| Tool | ID | Risk | Capability |
|------|-----|------|------------|
| Safe Test | `demo.safe_test` | SAFE | `safe_test` |

Execution flow:

```text
Command (TOOL_EXECUTE)
    → authorize_tool_execution()
    → ToolRegistry.resolve_executable()
    → AgentGateway.send_tool_execute()
    → PC Agent LocalToolDispatcher
    → registered handler
    → tool_execute_result
    → RepairSession broadcast
```

Tipi futuri (non eseguibili ancora): microscope, thermal_camera, multimeter, power_supply, 3utools, borneo, zxw, alpilab_check.

`ToolRegistry` — in-memory; rifiuta tool sconosciuti (`TOOL_NOT_FOUND`).

---

## 11. Alpilab Hub

Mantenuto separato in `hub/`. Cloud non controlla hardware direttamente.

```text
ALPILAB AI CLOUD → ALPILAB HUB → Windows + strumenti/software
```

`AlpilabHub` + `MockAlpilabHub` — interfaccia esistente, usata da `CommandEngine` in mock.

---

## 12. Security model

**Layer:** `app/security/`

- `Permission`, `Capability`
- `ActionAuthorization` con `ActionRiskLevel`: `READ_ONLY`, `SAFE`, `CONFIRM_REQUIRED`, `DANGEROUS`
- Cambio dispositivo/sessione: **no conferma**
- Azioni hardware/software pericolose: **conferma richiesta** (classificazione, non esecuzione reale)

---

## 13. Future web/PWA architecture

**Frontend** (`frontend/`): React + TypeScript + Vite UI V0.1 (mock data only).

**Backend API** (`app/api/`): route registry — server HTTP non attivo.

**Prossima fase:** FastAPI + WebSocket, PWA manifest/service worker, PostgreSQL, auth.

---

## Frontend UI Architecture (V0.1)

**Stack:** React 18, TypeScript, Vite, CSS Modules, Vitest.

### Responsive strategy

Mobile-first; desktop breakpoint 1024px; safe-area per tastiera; `prefers-reduced-motion`.

### Component architecture

`components/` (core, chat, repair, tools, session, ui), `pages/`, `hooks/useRepairSession`, `mock/`, `api/` (future).

### Design tokens

`frontend/src/styles/tokens.css` — CSS variables per tema dark-first.

### Mock / API separation

UI V0.1 non chiama il backend; stato locale via hook + `mock/scenario.ts`.

### Multi-device UI mock

`SessionDevices` mostra PC/Phone/Tablet online/offline.

### PWA-ready

Viewport, theme-color; service worker non implementato.

---

## Stato implementazione (foundation)

| Componente | Stato |
|------------|--------|
| Repair schemas | ✅ Pydantic |
| Session multi-device | ✅ Mock store |
| Realtime events | ✅ In-memory manager |
| PC Agent V0.1 | ✅ Connected but idle (AGENT_TEST only) |
| PC Agent V0.2 | ✅ Safe tool execution (`demo.safe_test` pipeline) |
| PC Agent V0.3 | ✅ WindowsAppTool + `windows.3utools.open` (dry-run + execution) |
| Conversation/Command engine | ✅ Mock parser |
| Voice interfaces | ✅ Mock STT/TTS |
| Diagnostic state + anti-loop | ✅ |
| Tool registry | ✅ Mock |
| Security classification | ✅ |
| Hub / Check connectors | ✅ Mock |
| AI providers | ✅ Mock only |
| HTTP server / DB cloud | ❌ Pianificato |
| Frontend UI V0.1 | ✅ React mock UI |

## Evoluzione documentata

Modifiche strutturali significative devono essere motivate qui o in PR dedicati prima dell'implementazione.
