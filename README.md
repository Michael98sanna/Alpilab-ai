# Alpilab AI

Assistente tecnico AI cloud/web per laboratori di riparazione smartphone.

Alpilab AI è un progetto **separato** da [Alpilab Check](https://github.com/Michael98sanna/Alpilab-ai): non importa il codice interno di Alpilab Check e in futuro comunicherà con esso solo tramite un contratto dati/API stabile.

## Alpilab AI vs Alpilab Check

| | Alpilab Check | Alpilab AI |
|---|---------------|------------|
| Tipo | Applicazione Windows al banco | Web app cloud-first (futura PWA) |
| Uso principale | Identificazione e diagnostica al banco | Assistente tecnico AI multi-dispositivo |
| Accesso | PC Windows | PC, tablet, smartphone (iOS/Android) |
| Relazione | Progetto autonomo esistente | Nuovo progetto; bridge futuro via API |

## Obiettivo

Alpilab AI supporta i tecnici con:

- ragionamento su problemi tecnici
- knowledge base e RAG (futuro)
- più motori AI tramite router comune
- modelli locali e cloud intercambiabili
- storico riparazioni e memoria del laboratorio (futuro)
- integrazione con Alpilab Check, Hub e strumenti del banco (futuro)

## Architettura (overview)

```text
                    ALPILAB AI
                        |
                  AI Router
          _____________|_____________
         |             |             |
      Local AI      Online AI      Fallback
         |             |             |
         +_____________+_____________+
                       |
                Knowledge Base
                       |
             Repair History / RAG
                       |
              Alpilab Check Bridge
```

Dettagli completi: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Struttura repository

```text
alpilab-ai/
├── app/                    # Backend application
│   ├── api/                # Route registry + endpoint handlers (no HTTP server yet)
│   ├── conversation/       # ConversationCommandEngine + NL command service (V0.4)
│   ├── commands/           # CommandEngine + NaturalLanguageCommandParser (V0.4)
│   ├── diagnostics/        # DiagnosticStateManager + anti-loop
│   ├── realtime/           # RealtimeSessionManager + events
│   ├── agent/              # PC Agent gateway, registry, WS handler
│   ├── session/            # InMemorySessionStore + SessionResumeManager
│   ├── security/           # Permission / authorization model
│   ├── tools/              # Tool abstraction + registry
│   ├── voice/              # STT/TTS interfaces (mock)
│   ├── main.py             # Future HTTP server entry point
│   ├── core/               # Configurazione
│   ├── models/             # Futuro layer persistenza
│   ├── schemas/            # Modelli dati (repair + session + commands)
│   ├── services/           # Logica di business (futuro)
│   └── integrations/       # Alpilab Check bridge
├── ai/                     # AI layer
│   ├── providers/          # MockProvider (+ futuri provider)
│   ├── router.py           # AI Router
│   ├── prompts/            # Template di sistema
│   └── schemas.py          # AIRequest / AIResponse
├── knowledge/              # Futura knowledge base / RAG
├── frontend/               # Shell HTML + client API stub (no framework yet)
│   ├── public/
│   └── src/
├── hub/                    # Interfacce Alpilab Hub (mock)
├── pc_agent/               # PC Agent V0.4 (Windows process, safe + Windows app tools)
├── tests/                  # Test pytest
├── docs/                   # Documentazione
├── app.py                  # Entry point CLI
├── requirements.txt
├── .env.example
└── README.md
```

## Requisiti

- Python 3.10+
- pip

## Avvio

```bash
# Installazione dipendenze
pip install -r requirements.txt

# Configurazione locale (opzionale)
cp .env.example .env

# Backend realtime (FastAPI + WebSocket)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# CLI interattiva con MockProvider
python3 app.py
```

## Frontend (UI V0.3.1)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev      # http://localhost:5173
npm run build
npm test
```

### Modalità MOCK vs REALTIME

| Modalità | Config | Comportamento |
|----------|--------|---------------|
| **MOCK** (default) | `VITE_APP_MODE=mock` | UI con dati locali, nessun backend |
| **REALTIME** | `VITE_APP_MODE=realtime` | WebSocket verso backend, sessione condivisa |

Variabili frontend (`.env`):

```bash
VITE_APP_MODE=realtime
VITE_API_URL=http://127.0.0.1:8000
VITE_WS_URL=ws://127.0.0.1:8000
```

Entrare in una sessione condivisa via URL:

```text
http://localhost:5173/?session=repair-001
```

CORS backend: origini default `localhost:5173`. Aggiungere altre con `CORS_ORIGINS=http://192.168.1.10:5173`.

## Test backend

```bash
pip install -r requirements.txt
python3 -m pytest tests/ -v
```

## Test frontend

```bash
cd frontend && npm test
```

## Cosa è implementato

### Foundation (V1)
- Interfaccia astratta `AIProvider` + `MockProvider` + `AIRouter`
- Schemi Pydantic riparazione (`Device`, `RepairSession`, `DiagnosticTest`, …)
- `AlpilabCheckConnector` e `AlpilabHub` (interfaccia + mock)
- API route registry (`GET /health`, stub `POST /api/v1/ai/generate`) — senza server HTTP
- Frontend shell responsive + `AlpilabApiClient` stub

### UI V0.1 (React + TypeScript + Vite)
- Web app dark-first responsive (PC, tablet, smartphone)
- Alpilab Core, chat mock, diagnostica mock, strumenti contestuali
- Dati mock locali — nessuna API/backend integration
- Vitest per componenti principali

### Architecture V2 (session-centric)
- **Repair Session** come entità centrale multi-device (`User`, `ClientDevice`, `SessionParticipant`, `RepairSessionContext`)
- **RealtimeSessionManager** con eventi tipizzati (in-memory, futuro WebSocket)
- **ConversationCommandEngine** — testo e voce sullo stesso engine
- **CommandEngine** — separazione conversazione vs comando (`Intent`, `Command`, `Action`)
- **DiagnosticStateManager** + anti-loop (no ripetizione test validati)
- **Session event log** + `InMemorySessionStore` + `SessionResumeManager`
- **ToolRegistry** + modello `Tool`
- **Security model** — `ActionRiskLevel`, `ActionAuthorization`
- Mock voice (`SpeechToText`, `TextToSpeech`)

- Configurazione via `.env` (senza segreti nel repo)
- **163 test pytest** — tutti passing
- Documentazione: `docs/ARCHITECTURE.md` (V2)

### Realtime V1 (multi-device foundation)
- **FastAPI** server con `GET /health`, `POST /api/v1/sessions`, WebSocket `/ws/sessions/{session_id}`
- **RealtimeSessionManager** esteso: presence, chat broadcast, session snapshot, reconnect
- Eventi: `CHAT_MESSAGE`, `ASSISTANT_STATUS`, `DEVICE_*`, `DIAGNOSTIC_*`, `SESSION_SNAPSHOT`
- Frontend: `RealtimeClient`, `RealtimeProvider`, modalità MOCK/REALTIME
- Session resume via `localStorage` + `?session=` URL param

### Realtime V1.1 (shared session state)
- **Server = source of truth** per diagnostica, repair context, assistant status, pause/resume
- `state_version` monotono per ordinamento eventi e gap detection
- Eventi: `SESSION_STATE_UPDATED`, `STATE_UPDATE_REJECTED` (+ eventi V1)
- Snapshot completo su connect/reconnect (`request_snapshot`)
- Frontend: unico stato in `useRepairSession`; UI deriva da lì (no duplicazione)
- Outbound WS: `diagnostic_update`, `diagnosis_pause`, `repair_context_update`
- **71 test pytest** + **44 test frontend** — tutti passing

> **Chat realtime ≠ Session realtime.** La chat era già sincronizzata in V1; V1.1 sincronizza l'intero stato della RepairSession (diagnostica, contesto, AI status, pause).

### PC Agent V0.1 (connected but idle)
- **Processo Windows locale** (`pc_agent/`) — connessione persistente al backend
- WebSocket dedicato: `/ws/agent/{session_id}`
- Registrazione, heartbeat, reconnect con backoff, capability dichiarative
- **Un solo comando accettato:** `AGENT_TEST` (allowlist lato agent)
- **Nessuna esecuzione reale** di shell, subprocess, PowerShell o controllo hardware
- Backend: `AgentRegistry`, `AgentGateway`, eventi realtime `AGENT_CONNECTED` / `AGENT_DISCONNECTED`
- UI realtime: badge `PC Agent ● ONLINE` / `○ OFFLINE` in header
- Documentazione: [docs/PC_AGENT.md](docs/PC_AGENT.md)

### PC Agent V0.2 (safe tool execution)
- **Prima pipeline controllata:** Authorization → ToolRegistry → AgentGateway → PC Agent → tool registrato
- Comando `TOOL_EXECUTE` con envelope validato (`tool_id`, `arguments`)
- Unico tool eseguibile: `demo.safe_test` (risultato innocuo, nessun accesso OS)
- `LocalToolDispatcher` lato agent — solo tool pre-registrati, no shell/subprocess
- Idempotency (`request_id`), timeout (30s), audit events
- REST dev: `POST .../tools/demo.safe_test/execute`, `GET /api/v1/tools`
- Risultato broadcast alla RepairSession (`TOOL_EXECUTE_RESULT`) — smartphone incluso
- **Non implementato:** 3uTools, Borneo, ZXW, hardware, shell, integrazione conversazionale AI

Avvio PC Agent (Windows):

```powershell
set ALPILAB_WS_URL=ws://127.0.0.1:8000
set ALPILAB_SESSION_ID=repair-001
set ALPILAB_CAP_SAFE_TEST=true
python -m pc_agent
```

Test AGENT_TEST:

```bash
POST /api/v1/sessions/repair-001/agents/{agent_id}/test
```

Test SAFE_TEST (V0.2):

```bash
POST /api/v1/sessions/repair-001/agents/{agent_id}/tools/demo.safe_test/execute
```

### PC Agent V0.3 (WindowsAppTool — 3uTools)
- **WindowsAppTool** generico — 3uTools è prima istanza registrata (`windows.3utools.open`)
- Path eseguibile **solo in config locale** PC Agent — server invia solo `tool_id`
- **DRY_RUN** default (`ALPILAB_WINAPP_3UTOOLS_DRY_RUN=true`) — valida senza aprire
- **Execution** con `subprocess.Popen([path], shell=False)` — no shell/PowerShell
- Capability `windows_apps` + app locale abilitata richieste entrambe
- REST dev: `POST .../tools/windows.3utools.open/execute`
- **Non implementato:** Borneo, ZXW, process manager, conferma UI

Test 3uTools dry-run (PowerShell):

```powershell
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/v1/sessions/repair-001/agents/{agent_id}/tools/windows.3utools.open/execute"
```

### PC Agent V0.4 (Natural Language Commands — 3uTools)
- **Parser rule-based deterministico** — nessun LLM, nessun shell/path da testo utente
- Flusso chat: testo/voce → `NaturalLanguageCommandParser` → `Intent` → Authorization → ToolRegistry → AgentGateway → PC Agent
- Primo comando supportato: **"Aprimi 3uTools"** (e varianti) → `OPEN_APPLICATION` → `windows.3utools.open`
- Distinzione esplicita **CONVERSATION** vs **ACTION_COMMAND** — diagnostica conversazionale non apre app
- Ambiguità (`"Apri il programma"`) → chiarimento, nessuna esecuzione
- Comandi non supportati (`"Apri Borneo"`, `"Chiudi 3uTools"`, path `.exe`, PowerShell) → rifiuto strutturato
- Integrazione **RepairSession** realtime: stati assistant THINKING → WORKING → SPEAKING
- **163 test pytest** — tutti passing
- Documentazione: [docs/PC_AGENT.md](docs/PC_AGENT.md) (sezione V0.4)

Test manuale chat (smartphone o frontend REALTIME su `?session=repair-001`):

```text
Aprimi 3uTools
```

Atteso: THINKING → WORKING → "Ho aperto 3uTools." (o messaggio dry-run se configurato).

## Cosa è pianificato (prossime fasi)

- Autenticazione e gestione utenti
- Deploy cloud e database PostgreSQL
- Provider AI reali (OpenAI, Gemini, Anthropic, modelli locali)
- Knowledge base, RAG e storico riparazioni
- Integrazione reale con Alpilab Check e Alpilab Hub
- Controllo hardware (microscopio, termocamera, multimetro, alimentatore)
- Integrazione 3uTools, Borneo, ZXW
- Assistente vocale (STT/TTS reali)
- QR code / pair device

## Regole del progetto

1. Nessuna API key nel repository.
2. I provider AI devono essere intercambiabili.
3. La logica tecnica non deve dipendere dal provider scelto.
4. Alpilab Check: solo tramite interfaccia dati separata.
5. Risposte tecniche: distinguere fatti, dati rilevati, ipotesi e confidenza.
6. Prima di automatizzare una diagnosi: proporre controlli verificabili.
7. Nessuna esecuzione arbitraria di comandi o remote shell dall'Hub.

## Licenza

Da definire.
