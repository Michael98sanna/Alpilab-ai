# Alpilab AI

Assistente tecnico AI **cloud-first** per laboratori di riparazione smartphone.

Accessibile da PC Windows, smartphone Android/iPhone e tablet Android/iPad (web, futura PWA).

## Cos'è Alpilab AI

Alpilab AI è un sistema web/cloud che aiuta i tecnici a:

- ragionare su problemi di riparazione;
- usare modelli AI intercambiabili (locale o cloud) tramite un AI Router;
- conservare in futuro storico riparazioni, foto, misure e knowledge base;
- dialogare in futuro con il PC di laboratorio tramite **Alpilab Hub**.

Non costruisce un nuovo modello AI: orchestra modelli esistenti dietro un'interfaccia unica.

## Differenza rispetto ad Alpilab Check

| | **Alpilab Check** | **Alpilab AI** |
|---|---|---|
| Tipo | App Windows al banco | Web app cloud-first |
| Uso principale | Identificazione e diagnostica sul PC | Assistenza AI da qualsiasi device |
| Codice | Repository separata | Questa repository |
| Integrazione | — | Solo tramite API/bridge futuro |

**Alpilab AI non importa codice interno di Alpilab Check.**  
In futuro comunicheranno tramite un contratto dati stabile (`AlpilabCheckConnector`).

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
```

Dettaglio: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Struttura repository

```text
alpilab-ai/
├── app/                 # Backend applicazione
│   ├── api/             # Endpoint HTTP (FastAPI)
│   ├── core/            # Config, sicurezza
│   ├── models/          # Persistenza futura
│   ├── schemas/         # Contratti dati riparazione
│   ├── services/        # Logica applicativa
│   └── integrations/    # Bridge Alpilab Check (mock)
├── ai/                  # Layer AI (provider + router)
│   ├── providers/       # AIProvider + MockProvider
│   ├── prompts/
│   ├── router.py
│   └── schemas.py
├── knowledge/           # Knowledge base (placeholder)
├── frontend/            # UI web/PWA (placeholder)
├── hub/                 # Alpilab Hub (interfacce + mock)
├── tests/
├── docs/
├── app.py               # CLI + avvio server
├── requirements.txt
├── .env.example
└── README.md
```

## Requisiti

- Python 3.11+ (testato su 3.12)
- Nessuna API key obbligatoria in questa fase

## Avvio

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### CLI interattiva (MockProvider)

```bash
python app.py
```

### API HTTP locale

```bash
python app.py --serve
# oppure: uvicorn app.main:app --reload
```

- Health: `GET http://127.0.0.1:8000/api/health`
- Ask: `POST http://127.0.0.1:8000/api/ai/ask`
- Docs: `http://127.0.0.1:8000/docs`

Esempio:

```bash
curl -s http://127.0.0.1:8000/api/ai/ask \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"iPhone non si accende"}'
```

## Test

```bash
pytest
```

I test verificano: MockProvider, AI Router, Device, RepairSession, DiagnosticTest, Measurement, AlpilabCheckConnector mock, AlpilabHub mock.

## Cosa è implementato (fase fondazione)

- Struttura modulare cloud-first
- Astrazione `AIProvider` (`generate`, `generate_with_image`, `generate_stream`, `is_available`)
- `MockProvider` chiaramente identificato come mock
- `AIRouter` con hook per routing futuro (locale/cloud/fallback/capacità)
- Schemi dati: Device, RepairSession, CustomerIssue, DiagnosticTest, Measurement, Diagnosis, RepairAction, RepairResult, ImageAttachment, Note
- `AlpilabCheckConnector` + mock (nessun codice Check)
- `AlpilabHub` + mock (nessuna esecuzione OS / remote shell)
- API FastAPI minimale (`/api/health`, `/api/ai/ask`)
- Config via `.env` (senza segreti nel repo)
- Gate di conferma per azioni Hub potenzialmente pericolose

## Cosa è pianificato (non in questa fase)

- Autenticazione completa e multi-utente
- Provider reali (OpenAI, Anthropic, Google, modelli locali)
- PostgreSQL / storage file in produzione
- RAG e knowledge base operativa
- Visione / annotazione immagini avanzata
- Voce / hands-free
- Controllo hardware reale via Hub
- Integrazioni 3uTools / Borneo / ZXW
- Bridge reale con Alpilab Check
- Deploy cloud e PWA installabile

## Sicurezza

1. Nessuna API key o password nel repository
2. `.env` ignorato da git; usare `.env.example` come template
3. Nessuna esecuzione arbitraria di comandi
4. Hub: niente remote shell; azioni rischiose richiederanno conferma esplicita
5. I provider AI sono intercambiabili: nessun lock-in al codice applicativo

## Principio AI

Il resto dell'applicazione **non sa** se la risposta arriva da un modello locale o cloud.  
Tutti i provider implementano la stessa interfaccia astratta.
