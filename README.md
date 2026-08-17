"""ALPILAB AI

Assistente tecnico AI **cloud-first** per laboratorio di riparazione smartphone.

Progetto **separato** da Alpilab Check.

## Cos'è Alpilab AI

Alpilab AI è un sistema web/cloud accessibile da PC, smartphone e tablet.
Usa modelli AI **esistenti e intercambiabili** (niente lock-in su un solo vendor)
per supportare diagnosi, knowledge base, storico riparazioni e — in futuro —
integrazioni con hardware/software di banco tramite Alpilab Hub.

## Differenza rispetto ad Alpilab Check

| | **Alpilab Check** | **Alpilab AI** |
|---|---|---|
| Tipo | App Windows al banco | Web/cloud (futura PWA) |
| Uso principale | Identificazione e diagnostica device | Assistente AI tecnico + knowledge |
| Accesso | PC laboratorio | PC, Android, iPhone, tablet, iPad |
| Relazione | Progetto autonomo | Si collegherà a Check solo via API/bridge |

**Questa repository non importa e non modifica Alpilab Check.**

## Architettura (sintesi)

```text
Web / PWA  →  API (FastAPI)  →  Services  →  AI Router  →  AIProvider
                                      ↓
                               Domain models
                                      ↓
                    Check connector (mock) | Hub (mock)
```

Dettaglio: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Struttura repository

```text
alpilab-ai/
├── app/                 # Backend applicativo
│   ├── api/             # Route HTTP
│   ├── core/            # Config + security stubs
│   ├── models/          # Contratti dominio riparazioni
│   ├── schemas/         # DTO / re-export
│   ├── services/        # Orchestrazione
│   └── integrations/    # Bridge verso sistemi esterni (Check)
├── ai/                  # Layer AI (provider + router + prompts)
├── knowledge/           # Futura knowledge base / RAG
├── frontend/            # Futura UI web/PWA
├── hub/                 # Astrazioni Alpilab Hub (mock)
├── tests/
├── docs/
├── app.py               # Entry CLI / avvio API
├── requirements.txt
└── .env.example
```

## Requisiti

- Python 3.11+
- `pip install -r requirements.txt`

## Configurazione

```bash
cp .env.example .env
```

Non inserire API key reali nel repository. `.env` è gitignored.

## Avvio

CLI di smoke test (MockProvider):

```bash
python app.py
```

API HTTP:

```bash
python app.py --api
# oppure
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoint utili:

- `GET /api/health`
- `POST /api/ai/ask` — body: `{"question": "..."}`
- `GET /api/ai/provider`
- Docs interattive: `http://localhost:8000/docs`

## Test

```bash
pytest -q
```

## Cosa è implementato (fase 1)

- Interfaccia astratta `AIProvider` (`generate`, `generate_with_image`, `generate_stream`, `is_available`)
- `MockProvider` chiaramente etichettato
- `AIRouter` con injection + slot per fallback futuri
- Modelli dominio: Device, RepairSession, CustomerIssue, DiagnosticTest, Measurement, Diagnosis, RepairAction, RepairResult, ImageAttachment, Note
- `AlpilabCheckConnector` + mock (nessun codice Check)
- `AlpilabHub` + mock (nessun controllo Windows/hardware reale)
- API FastAPI minima health + ask
- Config via `.env` / `.env.example`
- Test iniziali sui punti sopra

## Cosa è pianificato (non in questa fase)

- Auth completa, deploy cloud, DB PostgreSQL live
- Provider AI reali (OpenAI, Google, Anthropic, locali)
- RAG / knowledge indexing
- Integrazione reale Check / Hub / 3uTools / Borneo / ZXW
- Hardware (microscopio, termocamera, multimetro, alimentatore)
- Voce, PWA installabile, computer vision avanzata
- Permessi operatori completi (già previsti stub di conferma per azioni pericolose)

## Regole

1. Nessuna API key nel codice
2. Provider AI intercambiabili
3. Nessuna dipendenza dal codice interno di Alpilab Check
4. Mock e placeholder devono essere evidenti
5. Niente remote shell / comandi arbitrari
6. Prima di cambiare architettura, aggiornare `docs/ARCHITECTURE.md`
