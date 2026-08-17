# Architettura Alpilab AI

Documento di riferimento per la visione a lungo termine e lo stato della fondazione attuale.

## Visione complessiva

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

Alpilab AI è **cloud-first**: non è un'app desktop. Il frontend web (e futura PWA) parla con un backend API. Alpilab Hub sarà un servizio Windows opzionale che fa da ponte sicuro verso software/hardware di laboratorio.

## Separazione dei confini

| Componente | Responsabilità | Dipendenza da Check |
|---|---|---|
| **Alpilab AI** | Assistente AI, API, KB, storico, UI web | Nessuna dipendenza di codice |
| **Alpilab Check** | App Windows al banco (progetto separato) | N/A |
| **Alpilab Hub** | Ponte PC ↔ cloud (futuro) | Opzionale, via contratto |
| **Check Bridge** | Connettore astratto AI ↔ Check | Solo API/file/HTTP/local bridge |

**Regola:** Alpilab AI non importa moduli interni di Alpilab Check e non modifica quella repository.

## Layer applicativi

### Frontend
- Web responsive (PC / tablet / smartphone)
- Futura PWA installabile
- Nella fondazione: placeholder statico in `frontend/`

### Backend (`app/`)
- FastAPI
- Autenticazione / utenti (futuro)
- Riparazioni, dispositivi, file, AI, integrazioni
- Config via environment (`.env`)

### AI Layer (`ai/`)
- `AIProvider`: interfaccia comune
- Provider locali e cloud (futuri) dietro la stessa API
- `AIRouter`: selezione provider (oggi: MockProvider)
- Prompt versionati in `ai/prompts/`

Criteri di routing previsti (non ancora implementati in modo complesso):

- locale vs cloud
- fallback
- tipo richiesta / presenza immagini
- costo / capacità / disponibilità

### Database
- Produzione: PostgreSQL
- Sviluppo: SQLite opzionale
- Nella fondazione: modelli Pydantic + store in-memory per smoke API

### Storage
- Foto, immagini annotate, documenti, manuali, schemi, file diagnostici
- Path configurabile (`STORAGE_ROOT`) — non ancora un object store

### Knowledge (`knowledge/`)
- Placeholder per KB tecnica e RAG futuro
- Memoria soluzioni di laboratorio (futuro)

### Hub (`hub/`)
Interfaccia concettuale con capability:

- `open_application` / `close_application`
- `capture_microscope` / `capture_thermal_camera`
- `read_multimeter` / `read_power_supply`
- `get_pc_status`

**Vincoli di sicurezza:** nessun remote shell, nessuna esecuzione arbitraria, conferma esplicita per azioni pericolose.

## Contratto dati comune

I modelli in `app/models/` sono il contratto concettuale condiviso tra AI, futuro Check bridge e Hub:

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

## Stato fondazione vs futuro

### Implementato ora
- Struttura modulare
- Provider abstraction + MockProvider
- Router minimale
- Modelli/schema riparazione
- API HTTP skeleton
- Mock Check connector
- Mock Hub + gate di conferma
- Test automatici
- Documentazione

### Non implementato (volontariamente)
- Auth completa, deploy, provider AI reali a pagamento
- Database cloud, RAG completo, voce, CV avanzata
- Controllo hardware/software reale
- Integrazioni 3uTools / Borneo / ZXW / Check reali
- Hub Windows eseguibile

## Motivi di eventuali cambiamenti architetturali

Prima di cambiare questa architettura, documentare qui:

1. **Problema** che la struttura attuale non risolve
2. **Alternativa** considerata
3. **Impatto** su confini AI / Check / Hub
4. **Compatibilità** con il principio di provider intercambiabili

Nessun cambio strutturale rilevante è stato necessario rispetto al brief iniziale in questa fondazione.
