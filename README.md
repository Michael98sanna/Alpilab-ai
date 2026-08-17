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
│   ├── conversation/       # ConversationCommandEngine (text + voice)
│   ├── commands/           # CommandEngine + MockCommandParser
│   ├── diagnostics/        # DiagnosticStateManager + anti-loop
│   ├── realtime/           # RealtimeSessionManager + events
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

# CLI interattiva con MockProvider
python3 app.py
```

## Test

```bash
pip install -r requirements.txt
python3 -m pytest tests/ -v
```

## Cosa è implementato

### Foundation (V1)
- Interfaccia astratta `AIProvider` + `MockProvider` + `AIRouter`
- Schemi Pydantic riparazione (`Device`, `RepairSession`, `DiagnosticTest`, …)
- `AlpilabCheckConnector` e `AlpilabHub` (interfaccia + mock)
- API route registry (`GET /health`, stub `POST /api/v1/ai/generate`) — senza server HTTP
- Frontend shell responsive + `AlpilabApiClient` stub

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
- **46 test pytest** — tutti passing
- Documentazione: `docs/ARCHITECTURE.md` (V2)

## Cosa è pianificato (non in questa fase)

- Server HTTP reale (FastAPI) + WebSocket realtime
- Framework UI completo + PWA installabile
- Autenticazione e gestione utenti
- Deploy cloud e database PostgreSQL
- Provider AI reali (OpenAI, Gemini, Anthropic, modelli locali)
- UI completa, framework frontend e PWA installabile
- Knowledge base, RAG e storico riparazioni
- Integrazione reale con Alpilab Check e Alpilab Hub
- Controllo hardware (microscopio, termocamera, multimetro, alimentatore)
- Integrazione 3uTools, Borneo, ZXW
- Assistente vocale

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
