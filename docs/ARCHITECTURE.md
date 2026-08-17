"""
# Architettura Alpilab AI

Documento di riferimento per l'architettura prevista.
La fase attuale implementa solo la fondazione modulare (mock / interfacce).

## Visione d'insieme

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
                           |
                    ALPILAB HUB
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

## Separazione dei prodotti

| Prodotto | Ruolo |
|----------|--------|
| **Alpilab AI** | Sistema cloud/web: assistente tecnico, KB, storico, API |
| **Alpilab Check** | App Windows al banco: identificazione e diagnostica |
| **Alpilab Hub** | Futuro ponte Windows tra cloud e hardware/software del PC |

Alpilab AI **non** importa codice interno di Alpilab Check.
L'integrazione futura avverrà tramite contratto dati stabile (API / bridge / export).

## Layer applicativi

### Frontend (`frontend/`)
- Web application responsive (PC, tablet, smartphone)
- Futura PWA installabile
- In questa fase: solo placeholder

### Backend (`app/`)
- `api/` — futura API HTTP (health helper presente)
- `core/` — configurazione e policy di sicurezza
- `models/` — modelli di dominio riparazioni
- `schemas/` — contratti serializzabili condivisi
- `services/` — orchestrazione applicativa
- `integrations/` — connettori esterni (Check bridge)

### AI Layer (`ai/`)
- `providers/` — interfaccia `AIProvider` + `MockProvider`
- `router.py` — selezione provider (oggi: mock)
- `prompts/` — template provider-agnostic
- `schemas.py` — `AIRequest` / `AIResponse`

Principio: l'applicazione non sa se la risposta arriva da un modello locale o cloud.

### Knowledge (`knowledge/`)
- Astrazione KB + mock in-memory
- RAG completo: non implementato

### Hub (`hub/`)
- Interfaccia `AlpilabHub` + `MockAlpilabHub`
- Capability previste: open/close app, microscopio, termocamera, multimetro, PSU, status PC
- **Nessuna** esecuzione reale di programmi Windows o shell arbitraria

## Contratto dati riparazioni

Modelli concettuali (condivisi come contratto futuro tra AI / Check / Hub):

- `Device`
- `RepairSession`
- `CustomerIssue`
- `DiagnosticTest`
- `Measurement`
- `Diagnosis`
- `RepairAction`
- `RepairResult`
- `ImageAttachment`
- `Note`

Persistenza: non collegata in questa fase (servizio in-memory per test).

## AI Router — estensioni previste

Il router è predisposto (ma non implementa ancora logiche complesse) per:

- provider locale / cloud
- fallback
- scelta per tipo di richiesta
- scelta per costo
- scelta per capacità
- scelta per presenza di immagini
- scelta per disponibilità

## Sicurezza

- Nessuna API key nel repository
- Segreti solo via `.env` (ignorato da git); template in `.env.example`
- Hub: azioni potenzialmente pericolose disabilitate di default
- Conferma esplicita richiesta per azioni pericolose (quando abilitate)
- Vietata l'esecuzione arbitraria di comandi

## Database e storage (previsti)

- Produzione: PostgreSQL
- Sviluppo locale: SQLite opzionale
- Storage file: foto, annotazioni, documenti, schemi, diagnostica

## Cosa NON è in scope in questa fase

- Autenticazione completa
- Deploy cloud
- Provider AI reali (OpenAI, Gemini, Anthropic, locali)
- Database cloud
- Controllo hardware reale
- Integrazioni 3uTools / Borneo / ZXW
- Voce / computer vision avanzata / RAG completo
- Alpilab Hub Windows service reale

## Motivo di eventuali scostamenti strutturali

La struttura richiesta è rispettata. Eventuali aggiunte minime:

- `app/core/config.py` e `security.py` per centralizzare env e policy Hub
- `app/services/` per isolare orchestrazione da router/provider
- schemas dataclass invece di ORM: nessun DB obbligatorio in fondazione

Se in futuro si introduce FastAPI/SQLAlchemy, i contratti in `schemas/` restano il confine stabile.
"""
