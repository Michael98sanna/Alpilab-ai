# Alpilab AI

Assistente tecnico AI per un laboratorio di riparazione smartphone.

Alpilab AI è un’applicazione **cloud-first**: un backend HTTP e un frontend web
responsive, utilizzabili da PC Windows, smartphone, tablet, iPhone e iPad.
Non è un’applicazione desktop.

## Differenza rispetto ad Alpilab Check

| | **Alpilab Check** | **Alpilab AI** |
| --- | --- | --- |
| Cos’è | Applicazione Windows già in uso al banco | Sistema web/cloud nuovo e **separato** |
| Uso principale | Identificazione e diagnostica sul PC del laboratorio | Assistente tecnico AI, storico, knowledge, integrazioni future |
| Codice | Repository autonoma | Questa repository. **Non importa codice di Check** |
| Collegamento futuro | Espone dati tramite un contratto/API | `AlpilabCheckConnector`: ponte HTTP/file/Hub, non un import interno |

Le due applicazioni resteranno indipendenti. In futuro comunicheranno tramite
un’interfaccia stabile (API, file o bridge locale), senza condividere moduli.

## Architettura (fase attuale)

```text
  PC / tablet / smartphone
            |
         Web UI
            |
      FastAPI (app/)
            |
     AssistantService
            |
        AI Router
            |
      MockProvider   ← unico provider implementato
            |
     modelli dati (contratto comune futuro con Check e Hub)
```

La visione a lungo termine (Hub, hardware, RAG, voce, provider cloud) è
descritta in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). **Non è
implementata in questa fase.**

## Struttura del repository

```text
alpilab-ai/
├── app/                  Backend HTTP
│   ├── api/              Route FastAPI
│   ├── core/             Configurazione e sicurezza
│   ├── models/           Contratto dati (Device, RepairSession, …)
│   ├── schemas/          DTO HTTP
│   ├── services/         Casi d’uso
│   └── integrations/     Ponti verso Check e Hub
├── ai/                   Layer AI agnostico dal vendor
│   ├── providers/        Interfaccia + MockProvider
│   ├── prompts/
│   ├── router.py
│   └── schemas.py
├── knowledge/            Placeholder per futura KB / RAG
├── frontend/             UI web minimale
├── hub/                  Contratto del futuro servizio Windows
├── tests/
├── docs/
├── .env.example
├── app.py                Avvio del server HTTP
├── requirements.txt
└── README.md
```

## Come avviare il progetto

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Apri `http://127.0.0.1:8000/` per la UI e `http://127.0.0.1:8000/docs` per
OpenAPI.

CLI di sviluppo (stesso MockProvider, senza browser):

```bash
python -m app.cli
```

## Come eseguire i test

```bash
pip install -r requirements.txt
pytest
```

I test coprono MockProvider, AI Router, schemi Device / RepairSession /
DiagnosticTest / Measurement, connettori mock di Alpilab Check e Alpilab Hub.

## Cosa è implementato

- Interfaccia `AIProvider` (`generate`, `generate_with_image`, `generate_stream`, `is_available`)
- `MockProvider` chiaramente etichettato, senza chiamate esterne
- `AIRouter` con selezione minimale e hook per policy future
- Modelli/contratto: Device, RepairSession, CustomerIssue, DiagnosticTest,
  Measurement, Diagnosis, RepairAction, RepairResult, ImageAttachment, Note
- API HTTP (`/api/v1/health`, `/api/v1/assistant/ask`)
- Frontend web responsive di base
- Astrazione `AlpilabCheckConnector` (solo mock)
- Astrazione `AlpilabHub` (solo mock: nessuna shell, nessun programma Windows)
- Permessi e conferma esplicita per azioni Hub potenzialmente pericolose
- Configurazione da `.env` (`.env` è gitignored)

## Cosa è pianificato (non presente)

- Autenticazione completa e multi-utente
- Provider reali (OpenAI, Google, Anthropic, modelli locali)
- Policy di routing avanzata (costo, fallback, tipo richiesta)
- Database PostgreSQL / SQLite persistente
- Knowledge base, RAG, storico operativo
- Analisi immagini, annotazioni, voce
- Integrazione reale con Alpilab Check, 3uTools, Borneo, ZXW
- Hub Windows collegato a microscopio, termocamera, multimetro, alimentatore
- PWA installabile, deploy cloud

## Sicurezza (regole già in vigore)

1. Nessuna API key o password nel repository.
2. I segreti stanno in `.env`, mai committato.
3. Nessun provider AI è obbligatorio: il resto dell’app parla solo con `AIProvider`.
4. Nessuna esecuzione arbitraria di comandi.
5. Le azioni Hub pericolose richiedono permesso **e** `confirmed=True`.
6. Il mock Hub rifiuta nomi che non sono nella allow-list logica (`3utools`, …):
   non è uno shell remoto.

## Licenza / stato

Progetto interno di laboratorio, fase **foundation**. Eseguibile in locale
con il provider mock; non è pronto per la produzione.
