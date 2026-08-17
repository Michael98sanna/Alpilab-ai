# Architettura Alpilab AI

Questo documento descrive l'architettura prevista di Alpilab AI e lo stato attuale della fondazione.

## Visione

Alpilab AI è un assistente tecnico cloud/web per un laboratorio di riparazione smartphone. È un progetto **separato** da Alpilab Check: non importa il codice interno di Alpilab Check e comunica con esso solo tramite contratti dati/API futuri.

## Contesto nel laboratorio

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

## Principi architetturali

1. **Cloud-first**: web application responsive, futura PWA installabile su PC, tablet e smartphone.
2. **Provider AI intercambiabili**: tutti i provider implementano la stessa interfaccia astratta; l'applicazione non deve sapere se la risposta arriva da un modello locale o cloud.
3. **Separazione da Alpilab Check**: integrazione solo tramite `AlpilabCheckConnector` (API, file, bridge locale).
4. **Hub locale opaco**: `AlpilabHub` è il futuro ponte Windows tra cloud e hardware/software del banco, senza remote shell o esecuzione arbitraria di comandi.
5. **Sicurezza**: nessuna credenziale nel repository; configurazione via `.env`; azioni hardware future con permessi e conferma esplicita.

## Layer dell'applicazione

### Frontend (`frontend/`)

Placeholder per la futura web app responsive e PWA. Non implementato in questa fase.

### Backend (`app/`)

- `api/` — futuri endpoint HTTP per client web/mobile
- `core/` — configurazione e utilità condivise
- `schemas/` — modelli Pydantic (contratto dati condiviso)
- `services/` — logica di business (futuro)
- `integrations/` — connettori esterni (es. Alpilab Check)

### AI Layer (`ai/`)

- `providers/` — implementazioni provider (`MockProvider` attivo)
- `router.py` — selezione del provider (logica semplice, estendibile)
- `schemas.py` — `AIRequest`, `AIResponse`, capabilities
- `prompts/` — template di sistema

### Knowledge (`knowledge/`)

Placeholder per knowledge base tecnica, RAG e memoria delle soluzioni del laboratorio.

### Hub (`hub/`)

Interfacce per Alpilab Hub (Windows):

- `open_application` / `close_application`
- `capture_microscope` / `capture_thermal_camera`
- `read_multimeter` / `read_power_supply`
- `get_pc_status`

Solo mock in questa fase.

## Modello dati di riparazione

Entità definite in `app/schemas/repair.py`:

| Entità | Ruolo |
|--------|--------|
| `Device` | Dispositivo in riparazione |
| `RepairSession` | Sessione di riparazione (contenitore) |
| `CustomerIssue` | Problema segnalato dal cliente |
| `DiagnosticTest` | Test diagnostico verificabile |
| `Measurement` | Misura (multimetro, alimentatore, termocamera, ecc.) |
| `Diagnosis` | Ipotesi o conclusione tecnica |
| `RepairAction` | Azione di riparazione eseguita o pianificata |
| `RepairResult` | Esito finale |
| `ImageAttachment` | Foto o scansione collegata |
| `Note` | Annotazione libera del tecnico |

Questi schemi sono il contratto futuro tra Alpilab AI, Alpilab Check e Alpilab Hub.

## AI Router (stato attuale)

Il router riceve un `AIRequest` e seleziona un provider disponibile. Oggi:

- usa sempre `MockProvider` se disponibile
- se la richiesta contiene immagini, preferisce provider con capability `IMAGE_INPUT`

Dimensioni di routing **pianificate** (non implementate):

- provider locale vs cloud
- fallback su errore o timeout
- scelta per tipo di richiesta, costo, capacità, presenza di immagini

## Integrazioni future

| Componente | Interfaccia | Stato |
|------------|-------------|-------|
| Alpilab Check | `AlpilabCheckConnector` | Mock |
| Alpilab Hub | `AlpilabHub` | Mock |
| OpenAI / Gemini / Anthropic / locale | `AIProvider` | Mock |
| PostgreSQL | `DATABASE_URL` | Non implementato |
| Object storage | configurazione `.env` | Non implementato |
| RAG / Knowledge Base | `knowledge/` | Non implementato |
| Voce / visione avanzata | — | Non implementato |

## Sicurezza

- `.env` ignorato da git; `.env.example` senza segreti reali
- Nessuna API key nel codice
- Hub: nessuna esecuzione shell arbitraria; azioni pericolose richiederanno conferma
- Permessi granulari per azioni sul PC (futuro)

## Evoluzione documentata

Modifiche all'architettura devono essere motivate in questo file o in commit/PR dedicati prima di introdurre cambi strutturali significativi.
