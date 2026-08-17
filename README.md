# Alpilab AI

Assistente tecnico AI **cloud/web** per un laboratorio di riparazione smartphone.

Progetto **separato** da Alpilab Check (app Windows al banco). Alpilab AI non importa il codice interno di Alpilab Check e non lo modifica.

## Differenza tra Alpilab AI e Alpilab Check

| | **Alpilab Check** | **Alpilab AI** |
|---|---|---|
| Tipo | Applicazione Windows al banco | Sistema cloud/web (PC, tablet, smartphone) |
| Uso principale | Identificazione e diagnostica sul PC lab | Assistente tecnico AI, knowledge, storico, future integrazioni |
| Accesso | Desktop Windows | Browser / futura PWA |
| Integrazione | Autonomo | Futuro bridge API/file/HTTP verso Check e Hub |

## Architettura (fase fondazione)

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

Dettagli in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Struttura repository

```text
alpilab-ai/
├── app/                 # Backend FastAPI (api, core, models, schemas, services, integrations)
├── ai/                  # Provider abstraction, router, prompts, AI schemas
├── knowledge/           # Placeholder knowledge base / futuro RAG
├── frontend/            # Placeholder web statico
├── hub/                 # Interfacce + mock Alpilab Hub (nessun controllo reale)
├── tests/               # Pytest
├── docs/                # Documentazione architetturale
├── app.py               # CLI + avvio server
├── requirements.txt
├── .env.example
└── README.md
```

## Cosa è implementato

- Interfaccia astratta `AIProvider` (`generate`, `generate_with_image`, `generate_stream`, `is_available`)
- `MockProvider` chiaramente identificato come stub
- `AIRouter` con selezione base + hook per fallback futuri
- Modelli dati: `Device`, `RepairSession`, `CustomerIssue`, `DiagnosticTest`, `Measurement`, `Diagnosis`, `RepairAction`, `RepairResult`, `ImageAttachment`, `Note`
- API FastAPI minima: `/health`, `/api/ai/ask`, CRUD in-memory riparazioni
- `AlpilabCheckConnector` + `MockAlpilabCheckConnector` (nessun codice Check)
- `AlpilabHub` + `MockAlpilabHub` (nessuna esecuzione Windows / shell)
- Conferma obbligatoria per azioni Hub potenzialmente pericolose
- Config via `.env` / `.env.example` (nessun segreto nel repo)
- Test pytest per provider, router, modelli, Check mock, Hub mock

## Cosa è pianificato (non in questa fase)

Autenticazione completa, deploy cloud, provider AI reali, database cloud, RAG, voce, computer vision avanzata, controllo hardware/software reale, integrazioni 3uTools / Borneo / ZXW, Hub Windows completo, PWA installabile.

## Avvio

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# CLI interattiva (MockProvider)
python app.py

# Server API
python app.py --serve
# oppure: uvicorn app.api.main:app --reload
```

Apri:

- Health: http://127.0.0.1:8000/health
- OpenAPI: http://127.0.0.1:8000/docs
- Frontend placeholder: apri `frontend/index.html` nel browser

## Test

```bash
pytest -q
```

## Sicurezza

1. Nessuna API key nel repository.
2. `.env` è ignorato da git; usa solo `.env.example` come template.
3. Nessuna esecuzione arbitraria di comandi.
4. Azioni Hub future: permessi + conferma esplicita (`require_confirmation`).
5. Provider AI intercambiabili — nessun lock-in.

## Principio AI

Non costruiamo un modello da zero. Usiamo modelli esistenti dietro un'interfaccia comune. Il resto dell'app non sa se la risposta arriva da modello locale, OpenAI, Google, Anthropic o altro.
