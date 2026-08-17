# Architettura Alpilab AI

Questo documento descrive l'architettura **prevista** e lo stato **attuale**.
Le sezioni "futuro" non sono implementate: restano vincoli di progetto.

## 1. Posizionamento

Alpilab AI è una web application cloud-first. Non è un client desktop e non è un fork di Alpilab Check.

Client previsti:

- browser su PC Windows
- smartphone Android e iPhone
- tablet Android e iPad
- in seguito PWA installabile

Alpilab Check resta l'applicazione Windows di banco per identificazione e diagnostica. Alpilab AI non importa il suo codice interno.

## 2. Vista d'insieme (obiettivo a lungo termine)

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

## 3. Layer

### Frontend

Applicazione web responsive. Oggi: pagina statica di verifica in `frontend/`.
Domani: UI completa e PWA. Il frontend parla solo con l'API HTTP di Alpilab AI.

### Backend

API HTTP (FastAPI) per:

- salute del servizio
- richieste all'assistente (tramite AI Router)
- in seguito: autenticazione, utenti, riparazioni, dispositivi, file, integrazioni

Nessun database applicativo in questa fase. I modelli in `app/models/` sono il contratto, non uno schema ORM già persistito.

### AI layer

```text
Caller (API / servizio)
        |
        v
    AI Router
        |
        +-- MockProvider          (ora)
        +-- LocalProvider         (futuro)
        +-- CloudProvider(s)      (futuro)
```

Contratto obbligatorio per ogni provider:

- `name`
- `is_available()`
- `generate()`
- `generate_with_image()`
- `generate_stream()`

Il router può in futuro scegliere in base a:

- disponibilità
- locale vs cloud
- presenza di immagini
- tipo di richiesta
- costo
- capacità (testo, visione, streaming)
- fallback

Oggi la politica è minimale: primo provider disponibile, oppure il nome richiesto in `preferred_provider`.

### Database (futuro)

- PostgreSQL in produzione
- SQLite ammesso in sviluppo locale
- Non collegato in questa fase

### Storage (futuro)

Foto, immagini annotate, documenti, manuali, schemi, file diagnostici.
`ImageAttachment` descrive i metadati; i byte non stanno nei modelli di dominio.

### Knowledge (futuro)

RAG e memoria delle soluzioni di laboratorio. La cartella `knowledge/` esiste come confine di responsabilità, senza indicizzazione.

### Alpilab Hub (futuro servizio Windows)

Ponte tra cloud e il PC di laboratorio. Capacità previste dal contratto:

- `open_application` / `close_application` (id logici, non path o shell)
- `capture_microscope`
- `capture_thermal_camera`
- `read_multimeter`
- `read_power_supply`
- `get_pc_status`

Vincoli permanenti:

- nessuna remote shell
- nessuna esecuzione arbitraria di comandi
- permessi nominati per ogni azione
- conferma esplicita per azioni pericolose (es. chiusura applicazioni)

L'implementazione attuale è `MockAlpilabHub`.

### Bridge Alpilab Check (futuro)

`AlpilabCheckConnector` è un'interfaccia. Una futura implementazione potrà usare HTTP, file o il Hub locale. Non si assume l'architettura interna di Check.

## 4. Contratto dati

I modelli in `app/models/` sono il contratto comune tra Alpilab AI, Alpilab Check e Alpilab Hub:

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

`Diagnosis` separa `facts`, `hypotheses`, `evidence`, `confidence` e `recommended_checks`.

`RepairAction` prevede `requires_confirmation`, `is_potentially_dangerous` e `permission_required`.

## 5. Sicurezza (fin dall'inizio)

- Segreti solo in variabili d'ambiente / `.env`
- `.env` escluso da git
- Nessuna API key nel codice
- Hub e integrazioni non eseguono comandi
- Azioni Hub filtrate da `PermissionContext`
- Azioni pericolose bloccate senza `confirmed=True`

## 6. Cosa non fa questa fase

Non implementati di proposito:

- autenticazione
- deploy cloud
- provider AI a pagamento o SDK vendor
- database
- controllo hardware/software reale
- voce, computer vision, RAG completo

## 7. Come estendere (senza rompere i confini)

1. Nuovo provider AI: classe in `ai/providers/` che implementa `AIProvider`, poi registrazione nel router.
2. Persistenza: adattatori in `app/` che serializzano i modelli esistenti; non cambiare il contratto senza documentarlo.
3. Check reale: nuova classe che implementa `AlpilabCheckConnector`, senza importare Alpilab Check.
4. Hub reale: processo Windows separato che implementa `AlpilabHub`; il cloud resta un client dell'interfaccia.

Prima di cambiare questi confini, aggiornare questo documento con il motivo.
