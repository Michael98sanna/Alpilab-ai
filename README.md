# Alpilab AI

Assistente tecnico AI **cloud/web** per laboratorio di riparazione smartphone.

Progetto **separato** da Alpilab Check (applicazione Windows al banco). Alpilab AI non importa il codice interno di Alpilab Check e non lo modifica.

## Differenza rispetto ad Alpilab Check

| | **Alpilab Check** | **Alpilab AI** |
|---|---|---|
| Tipo | App Windows al banco | Sistema cloud/web (PC, Android, iPhone, tablet, futura PWA) |
| Uso principale | Identificazione e diagnostica dispositivo | Assistente tecnico AI, knowledge base, storico riparazioni |
| Integrazione | Prodotto autonomo | Futuro bridge tramite API/contratto stabile (`AlpilabCheckConnector`) |

## Architettura (visione)

```text
                    ALPILAB AI CLOUD
                           |
             +-------------+-------------+
             |             |             |
          AI Router    Knowledge Base   Database
             |             |             |
             +-------------+-------------+
                           |
                      Web / PWA
                           |
              +------------+------------+
              |            |            |
             PC         Tablet      Smartphone
                           |
                    ALPILAB HUB (futuro)
                           |
          +----------------+----------------+
          |                |                |
    Alpilab Check      Software          Hardware
                       3uTools            Microscopio
                       Borneo             Termocamera
                       ZXW                 Multimetro / PSU
```

Dettaglio: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Principio AI

Non costruiamo un modello da zero. Usiamo provider esistenti dietro un’interfaccia unica (`AIProvider`). L’applicazione non sa se la risposta arriva da mock, locale o cloud.

## Struttura repository

```text
alpilab-ai/
├── app/                 # Backend applicativo
│   ├── api/             # HTTP FastAPI (health + ask)
│   ├── core/            # Settings / .env
│   ├── models/          # Contratto dati riparazione
│   ├── schemas/         # DTO API
│   ├── services/        # Orchestrazione
│   └── integrations/    # Bridge Alpilab Check (interfaccia + mock)
├── ai/                  # Layer AI
│   ├── providers/       # AIProvider + MockProvider
│   ├── prompts/         # Template prompt
│   ├── router.py        # AI Router
│   └── schemas.py
├── knowledge/           # Placeholder knowledge base
├── frontend/            # Placeholder web/PWA
├── hub/                 # Alpilab Hub (interfaccia + mock, no shell)
├── tests/
├── docs/
├── app.py               # Entry CLI / --api
├── requirements.txt
├── .env.example
└── README.md
```

## Cosa è implementato (fase fondazione)

- Interfaccia `AIProvider` (`is_available`, `generate`, `generate_with_image`, `generate_stream`)
- `MockProvider` chiaramente identificato
- `AIRouter` con provider iniettabile e hook per fallback futuri
- Modelli dati: Device, RepairSession, CustomerIssue, DiagnosticTest, Measurement, Diagnosis, RepairAction, RepairResult, ImageAttachment, Note
- `AlpilabCheckConnector` + mock (nessun import da Alpilab Check)
- `AlpilabHub` + mock (nessuna esecuzione di programmi Windows / shell)
- API HTTP minima (`GET /health`, `POST /v1/ask`)
- CLI interattiva
- Test pytest per provider, router, modelli, connector, hub
- Configurazione via `.env` (senza segreti nel repo)

## Cosa è pianificato (non in questa fase)

Autenticazione completa, deploy cloud, provider AI reali (OpenAI/Gemini/…), DB cloud, RAG completo, hardware, 3uTools/Borneo/ZXW, voce, computer vision avanzata, Hub Windows reale, PWA.

## Avvio

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # opzionale
python app.py               # CLI con MockProvider
python app.py --api         # API su http://127.0.0.1:8000
```

Esempio API:

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/v1/ask \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"iPhone non si accende"}'
```

## Test

```bash
pytest -q
```

## Sicurezza

- Nessuna API key nel repository
- `.env` ignorato da git; usare `.env.example` come template
- Nessuna esecuzione arbitraria di comandi
- Azioni Hub future: allow-list + conferma esplicita per azioni potenzialmente pericolose

## Regole

1. Non implementare funzionalità future solo perché descritte.
2. Mock e placeholder devono essere evidenti.
3. Nessun lock-in a un singolo provider AI.
4. Nessuna dipendenza dal codice interno di Alpilab Check.
5. Backend predisposto per client web/mobile.
