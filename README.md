# Alpilab AI

Assistente tecnico AI cloud/web per laboratorio di riparazione smartphone.

Progetto **separato** da Alpilab Check.

## Cos'è Alpilab AI

Alpilab AI è un sistema cloud-first accessibile da PC, smartphone e tablet. Aiuta i tecnici a:

- ragionare su problemi di riparazione;
- usare modelli AI intercambiabili (locali o cloud) tramite un router comune;
- strutturare sessioni di riparazione, test e misure;
- preparare in futuro knowledge base, storico e integrazioni laboratorio.

Non costruisce un modello AI da zero: orchestra provider esistenti dietro un'interfaccia unica.

## Differenza rispetto ad Alpilab Check

| | Alpilab AI | Alpilab Check |
|---|---|---|
| Tipo | Web/cloud (futura PWA) | Applicazione Windows al banco |
| Uso | Assistente tecnico multi-dispositivo | Identificazione e diagnostica |
| Codice | Repository indipendente | Repository indipendente |
| Integrazione | Futuro bridge API/contratto dati | Espone dati via bridge (futuro) |

**Regola:** Alpilab AI non importa moduli interni di Alpilab Check.

## Architettura (sintesi)

```text
Web / PWA  →  Backend API  →  AI Router  →  Provider (mock | local | cloud)
                    ↓
              Models / KB / DB
                    ↓
              Alpilab Hub (futuro) → Check / tool / hardware
```

Dettaglio: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Struttura repository

```text
alpilab-ai/
├── app/                 # Backend applicativo
│   ├── api/             # Placeholder API + health
│   ├── core/            # Config e sicurezza
│   ├── models/          # Modelli di dominio
│   ├── schemas/         # Contratti serializzabili
│   ├── services/        # Orchestrazione
│   └── integrations/    # Bridge Alpilab Check (mock)
├── ai/                  # Layer AI (provider + router)
│   ├── providers/
│   ├── prompts/
│   ├── router.py
│   └── schemas.py
├── knowledge/           # KB astratta (mock)
├── frontend/            # Placeholder web/PWA
├── hub/                 # Alpilab Hub (interfacce + mock)
├── tests/
├── docs/
├── app.py               # Entry point CLI
├── requirements.txt
├── .env.example
└── README.md
```

## Avvio

Requisiti: Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # opzionale
python app.py
```

La CLI usa il `MockProvider` (nessuna API esterna).

## Test

```bash
pip install -r requirements.txt
pytest -q
```

I test coprono: MockProvider, AI Router, Device, RepairSession, DiagnosticTest, Measurement, Check connector mock, Hub mock.

## Cosa è implementato

- Interfaccia `AIProvider` (`generate`, `generate_with_image`, `generate_stream`, `is_available`)
- `MockProvider` offline
- `AIRouter` minimale con selezione del primo provider disponibile
- Modelli/schema riparazione (Device, RepairSession, test, misure, ecc.)
- `AlpilabCheckConnector` astratto + mock
- `AlpilabHub` astratto + mock (nessuna shell / nessun programma Windows)
- Config via ambiente + `.env.example`
- Policy sicurezza Hub (azioni pericolose disabilitate di default)
- Documentazione architetturale
- Test di fondazione

## Cosa è pianificato (non in questa fase)

- Autenticazione e deploy cloud
- Provider AI reali (OpenAI, Anthropic, Google, locali)
- PostgreSQL / storage cloud
- RAG e knowledge base completa
- Frontend web/PWA
- Hub Windows reale e hardware
- Integrazioni 3uTools / Borneo / ZXW / Check live
- Voce, computer vision avanzata, diagnosi guidata completa

## Sicurezza

1. Nessuna API key nel repository.
2. `.env` è ignorato da git; usare `.env.example` come template.
3. Provider AI intercambiabili — nessun lock-in.
4. Nessuna esecuzione arbitraria di comandi.
5. Azioni Hub pericolose: permesso + conferma esplicita (quando abilitate).

## Licenza / ownership

Progetto Alpilab — sviluppo interno laboratorio.
