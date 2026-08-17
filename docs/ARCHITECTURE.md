# Architettura Alpilab AI

Questo documento descrive l’architettura **prevista** e ciò che è **realmente
presente** nella fase foundation. Le sezioni “futuro” non sono implementate.

## 1. Posizionamento

Alpilab AI è un sistema cloud/web. I client sono browser su PC, tablet e
smartphone. Il backend espone un’API HTTP stabile.

Alpilab Check resta un’applicazione Windows autonoma, usata al banco per
identificazione e diagnostica. Alpilab AI **non** incorpora Check e **non**
ne importa il codice.

Alpilab Hub (futuro) sarà un servizio Windows sul PC del banco: ponte tra il
cloud e software/hardware locali.

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
                    ALPILAB HUB          ← futuro
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

## 2. Principio AI

Non addestriamo un modello da zero. Usiamo modelli esistenti, **intercambiabili**.

Il resto dell’applicazione non deve sapere se la risposta arriva da:

- un modello locale
- OpenAI
- Google
- Anthropic
- un altro provider

Tutti i backend implementano `ai.providers.base.AIProvider`:

- `name`
- `is_available()`
- `generate()`
- `generate_with_image()`
- `generate_stream()`

`AIRouter` è l’unico punto che sceglie il provider. In questa fase registra
solo `MockProvider`. La firma di `RoutingHints` prevede già (senza implementarli):

- preferenza locale / cloud
- costo
- presenza di immagini
- tipo di richiesta
- disponibilità
- fallback

Un provider reale verrà aggiunto come nuovo modulo in `ai/providers/`, senza
cambiare i servizi HTTP.

## 3. Layer attuali

| Layer | Percorso | Responsabilità |
| --- | --- | --- |
| Frontend | `frontend/` | UI web minimale, chiama l’API |
| HTTP | `app/api/` | REST versionato (`/api/v1`) |
| Servizi | `app/services/` | Casi d’uso; niente SDK vendor |
| Config / security | `app/core/` | `.env`, permessi, conferma esplicita |
| Contratto dati | `app/models/` | Device, sessioni, misure, diagnosi |
| DTO HTTP | `app/schemas/` | Request/response API |
| AI | `ai/` | Provider + router + prompt |
| Check | `app/integrations/alpilab_check.py` | Ponte futuro, oggi mock |
| Hub | `hub/` | Contratto del servizio Windows, oggi mock |
| Knowledge | `knowledge/` | Vuoto: futura RAG |

### Perché FastAPI

È una libreria matura, tipizzata, adatta a un backend usato da web e mobile.
Non introduce un frontend framework né un ORM: in questa fase non c’è un
database da mappare.

### Perché i modelli sono Pydantic e non tabelle

Il contratto comune tra AI, Check e Hub deve esistere **prima** della
persistenza. PostgreSQL (produzione) e SQLite (sviluppo) arriveranno quando
servirà lo storico, non per fingere un database oggi.

## 4. Contratto dati

`RepairSession` è l’aggregato: un lavoro su un `Device`, con issue del
cliente, test, misure, diagnosi, azioni, risultati, immagini e note.

Regole del contratto:

- I fatti e le ipotesi stanno in campi distinti (`Diagnosis.facts` vs
  `Diagnosis.hypotheses`).
- `DiagnosticTest.raw_payload` è opaco: AI non assume la forma interna di Check.
- `RepairAction.requires_confirmation` è vero di default. Un’azione pericolosa
  resta `proposed` finché `confirmed` non è esplicitamente `true`.
- `ImageAttachment` descrive metadati; lo storage file non è implementato.

Questi tipi sono il contratto. Quando Check o Hub invieranno dati, mapperanno
verso questi modelli, non il contrario.

## 5. Alpilab Check Connector

`AlpilabCheckConnector` è un port:

- `is_available()` / `get_info()`
- `import_device_identity()`
- `import_diagnostic_snapshot()`

Il trasporto (HTTP, file drop, Hub) **non è deciso**. Il mock accetta payload
già normalizzati in memoria. Non avvia Check, non legge il suo filesystem, non
ne conosce le classi interne.

## 6. Alpilab Hub

Hub espone **capability nominate**, non una shell:

- `get_pc_status`
- `open_application` / `close_application` (pericolose)
- `capture_microscope` / `capture_thermal_camera`
- `read_multimeter` / `read_power_supply`

Vincoli di sicurezza, già nel mock:

1. Ogni capability richiede un `PermissionContext`.
2. Le capability pericolose richiedono `confirmed=True`.
3. `open_application` accetta solo nomi logici in allow-list (`3utools`,
   `borneo`, `zxw`, `alpilab_check`), mai un path o un comando.
4. Il mock imposta sempre `executed=False`. Nessun processo viene lanciato.

Se in futuro Hub verrà estratto in un servizio Windows, i primitivi di
permesso oggi in `app/core/security.py` andranno con lui. Oggi vivono nel
monorepo per non duplicare regole.

## 7. Sicurezza

- Segreti solo in variabili d’ambiente (`.env` gitignored, `.env.example`
  senza valori reali).
- Nessun lock-in verso un vendor AI.
- Nessun remote command execution.
- CORS configurabile per client web/mobile.
- Autenticazione utenti: **non** in questa fase.

## 8. Evoluzione prevista (non fare ora)

1. Persistenza PostgreSQL e API delle sessioni di riparazione.
2. Primo provider reale dietro `AIProvider` (locale o cloud).
3. Policy di routing (fallback, immagini, costo).
4. Knowledge / RAG in `knowledge/`.
5. Storage file (foto, schemi, export diagnostici).
6. Implementazione Hub su Windows, con permessi per operatore.
7. Bridge Check → contratto dati.
8. PWA, voce, computer vision.

Ogni passo deve estendere un’interfaccia già presente, non aggirarla.
