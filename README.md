# Alpilab AI

Assistente tecnico AI **cloud-first** per laboratorio di riparazione smartphone.

Progetto **separato** da Alpilab Check.

## Cos'è Alpilab AI

Alpilab AI è una web application (API + futuro frontend/PWA) che:

- aiuta i tecnici con ragionamento diagnostico;
- userà più provider AI intercambiabili tramite un AI Router;
- conserverà (in futuro) storico riparazioni, foto e knowledge base;
- potrà comunicare con il PC di laboratorio tramite **Alpilab Hub**;
- potrà ricevere dati da **Alpilab Check** solo tramite un contratto/API stabile.

Non costruiamo un nuovo modello AI: orchestrami modelli esistenti dietro un'interfaccia unica.

## Differenza con Alpilab Check

| | Alpilab Check | Alpilab AI |
|---|---|---|
| Tipo | App Windows al banco | Sistema cloud/web |
| Uso | Identificazione e diagnostica device | Assistente AI, KB, storico, integrazioni |
| Client | PC Windows | PC, Android, iPhone, tablet, iPad |
| Codice | Repository separata | Questa repository |

**Regola:** Alpilab AI non importa codice interno di Alpilab Check. Integrazione futura solo via bridge/API.

## Architettura (sintesi)

```text
Web / PWA  →  Alpilab AI API  →  AI Router  →  Provider (mock oggi)
                      │
                      ├── Knowledge Base (futuro)
                      ├── Database (futuro)
                      ├── Alpilab Check Bridge (interfaccia)
                      └── Alpilab Hub (interfaccia)
```

Dettagli: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Struttura repository

```text
alpilab-ai/
├── app/                 # Backend FastAPI
│   ├── api/             # Endpoint HTTP
│   ├── core/            # Config / settings
│   ├── models/          # Alias dominio riparazione
│   ├── schemas/         # Contratti dati (Device, RepairSession, …)
│   ├── services/        # Logica applicativa
│   └── integrations/    # Bridge Alpilab Check (mock)
├── ai/                  # Layer AI (provider + router)
│   ├── providers/       # AIProvider + MockProvider
│   ├── prompts/
│   ├── router.py
│   └── schemas.py
├── knowledge/           # Placeholder KB / RAG
├── frontend/            # Placeholder web/PWA
├── hub/                 # Alpilab Hub (interfacce + mock)
├── tests/
├── docs/
├── .env.example
├── app.py               # CLI / avvio API
├── requirements.txt
└── README.md
```

## Requisiti

- Python 3.11+
- Ambiente virtuale consigliato

## Installazione

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Avvio

CLI di smoke-test (MockProvider):

```bash
python app.py
```

API HTTP:

```bash
python app.py --api
# oppure: uvicorn app.main:app --reload
```

Health check: `GET http://127.0.0.1:8000/health`  
Ask (mock): `POST http://127.0.0.1:8000/ai/ask` con body `{"prompt":"..."}`

## Test

```bash
pytest -q
```

## Cosa è implementato (fase fondazione)

- Astrazione `AIProvider` (`generate`, `generate_with_image`, `generate_stream`, `is_available`)
- `MockProvider` chiaramente etichettato
- `AIRouter` con selezione minimale e hook per routing futuro
- Schemi dominio riparazione (Device, RepairSession, DiagnosticTest, Measurement, …)
- `AlpilabCheckConnector` + mock (nessun import da Check)
- `AlpilabHub` + mock (nessuna esecuzione reale di programmi/shell)
- API FastAPI minimale (`/health`, `/ai/ask`)
- Config via `.env` / `.env.example`
- Test iniziali su provider, router, schemi, connector e hub

## Cosa è pianificato (non in questa fase)

- Autenticazione completa, deploy cloud, DB cloud
- Provider AI reali (OpenAI, Gemini, Anthropic, locali, …)
- RAG / knowledge base operativa
- Controllo hardware e software da Hub
- Integrazione reale con Check / 3uTools / Borneo / ZXW
- Voce, hands-free, computer vision avanzata
- Frontend/PWA completo

## Sicurezza

- Nessuna API key nel repository
- `.env` ignorato da git
- Nessuna remote shell / comandi arbitrari
- Azioni Hub pericolose: conferma esplicita obbligatoria (già nel mock)

## Licenza / ownership

Progetto privato Alpilab — sviluppo interno laboratorio.
