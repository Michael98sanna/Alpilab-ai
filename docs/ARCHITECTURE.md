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

## 4. Realtime events

**Layer:** `app/realtime/`

`RealtimeSessionManager` emette eventi a subscriber in-memory (futuro: WebSocket).

Eventi supportati (`RealtimeEventType`):

`SESSION_CREATED`, `SESSION_UPDATED`, `MESSAGE_CREATED`, `MESSAGE_UPDATED`, `AI_RESPONSE_STARTED`, `AI_RESPONSE_CHUNK`, `AI_RESPONSE_COMPLETED`, `VOICE_TRANSCRIPT`, `MEASUREMENT_CREATED`, `IMAGE_CREATED`, `IMAGE_UPDATED`, `ANNOTATION_CREATED`, `DIAGNOSTIC_TEST_UPDATED`, `TOOL_STATE_CHANGED`, `DEVICE_CONNECTED`, `DEVICE_DISCONNECTED`, `SESSION_RESUMED`

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

**Layer:** `app/tools/`

`Tool` generico: id, name, type, status, capabilities.

Tipi futuri: microscope, thermal_camera, multimeter, power_supply, 3utools, borneo, zxw, alpilab_check.

`ToolRegistry` — in-memory, no controllo reale.

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
