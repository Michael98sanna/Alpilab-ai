# Alpilab AI

Assistente tecnico AI per un laboratorio di riparazione smartphone.

Alpilab AI è un progetto **separato** da Alpilab Check: applicazione web cloud-first, accessibile da PC, smartphone e tablet. Non è un'applicazione desktop e non importa il codice interno di Alpilab Check.

## Differenza tra Alpilab AI e Alpilab Check

| | Alpilab Check | Alpilab AI |
|---|---|---|
| Tipo | Applicazione Windows già esistente | Sistema cloud/web |
| Uso principale | Banco: identificazione e diagnostica | Assistente tecnico, knowledge, storico |
| Accesso | PC Windows al banco | PC, Android, iPhone, tablet, iPad |
| Codice | Repository autonoma | Questa repository |
| Integrazione futura | Espone dati tramite API/file/bridge | Consuma un connettore, senza import interni |

Le due applicazioni potranno comunicare in futuro tramite un contratto dati stabile (modelli in `app/models/`). Alpilab Hub, previsto su PC Windows, farà da ponte verso hardware e software di laboratorio. **Hub e connettore Check sono solo interfacce/mock in questa fase.**

## Architettura

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
                    Windows PC
                           |
          +----------------+----------------+
          |                |                |
    Alpilab Check      Software          Hardware
                       3uTools            Microscopio
                       Borneo             Termocamera
                       ZXW                 Multimetro
                                           Alimentatore
```

Il resto dell'applicazione parla solo con l'**AI Router**. Non sa se la risposta arriva da un mock, da un modello locale o da un provider cloud. I provider reali non sono ancora collegati.

Dettaglio: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Struttura del repository

```text
alpilab-ai/
├── app/                  Backend (API, config, modelli, servizi, integrazioni)
│   ├── api/              Endpoint HTTP
│   ├── core/             Configurazione e primitive di sicurezza
│   ├── models/           Contratto dati condiviso (Device, RepairSession, ...)
│   ├── schemas/          Schema delle richieste HTTP
│   ├── services/         Casi d'uso applicativi
│   └── integrations/     Connettori verso sistemi esterni (solo interfacce)
├── ai/                   Layer AI (provider astratti + router)
│   ├── providers/        MockProvider; futuri provider locali/cloud
│   ├── prompts/          Template di prompt
│   ├── router.py
│   └── schemas.py
├── knowledge/            Knowledge base / RAG (non implementata)
├── frontend/             UI web minima, responsive
├── hub/                  Contratto Alpilab Hub (solo mock)
├── tests/
├── docs/
├── app.py                Avvio del server web
├── .env.example
├── requirements.txt
└── README.md
```

## Come avviare il progetto

Requisiti: Python 3.11 o successivo.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python3 app.py
```

Apri `http://127.0.0.1:8000/` nel browser.

- UI: `/`
- Health: `GET /api/health`
- Generazione AI (mock): `POST /api/ai/generate`

Esempio:

```bash
curl -s http://127.0.0.1:8000/api/health
curl -s -X POST http://127.0.0.1:8000/api/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"iPhone 12 non si accende"}'
```

Non sono richieste API key. Il provider attivo è `mock`.

## Come eseguire i test

```bash
pip install -r requirements.txt
python3 -m pytest
```

I test coprono MockProvider, AI Router, schemi Device / RepairSession / DiagnosticTest / Measurement, connettore Check mock e Hub mock.

## Cosa è implementato

- Struttura modulare backend + frontend web
- Interfaccia astratta `AIProvider` (`generate`, `generate_with_image`, `generate_stream`, `is_available`)
- `MockProvider` esplicitamente identificato come mock
- AI Router con selezione semplice (primo provider disponibile; preferenza per nome)
- Modelli dati: Device, RepairSession, CustomerIssue, DiagnosticTest, Measurement, Diagnosis, RepairAction, RepairResult, ImageAttachment, Note
- `AlpilabCheckConnector` + mock (nessun import da Alpilab Check)
- `AlpilabHub` + mock (nessuna esecuzione di programmi Windows o comandi shell)
- Permessi e conferma esplicita per azioni Hub potenzialmente pericolose
- Configurazione da `.env` (`.env` è ignorato da git)
- API HTTP minima e pagina web responsive di verifica

## Cosa è pianificato (non in questa fase)

- Autenticazione completa e gestione utenti
- Database PostgreSQL (o SQLite in sviluppo)
- Provider AI reali (OpenAI, Google, Anthropic, modelli locali)
- Routing avanzato (costo, capacità, fallback, locale/cloud)
- Knowledge base e RAG
- Storage file (foto, schemi, diagnostiche)
- Analisi immagini, annotazioni, visione artificiale
- Integrazione reale con Alpilab Check, 3uTools, Borneo, ZXW
- Hub Windows reale e controllo hardware
- Assistente vocale / hands-free
- Diagnosi guidata passo-passo
- PWA installabile
- Deploy cloud

## Sicurezza

- Nessuna API key o password nel repository
- Segreti solo in `.env` (non versionato)
- Nessuna esecuzione arbitraria di comandi
- Le future azioni hardware passeranno da permessi nominati
- Le azioni potenzialmente pericolose richiederanno `confirmed=True`

## Regole del progetto

1. Non costruire un nuovo modello AI: usare modelli esistenti, intercambiabili.
2. Il resto dell'app non deve dipendere dal provider scelto.
3. Alpilab Check resta un progetto autonomo.
4. Distinguere fatti, dati rilevati, ipotesi e livello di confidenza.
5. Prima di automatizzare una diagnosi, proporre controlli verificabili.
6. Mock e placeholder devono essere riconoscibili: non fingere integrazioni reali.
