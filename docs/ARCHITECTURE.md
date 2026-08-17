# Architettura Alpilab AI

Documento di riferimento per la fondazione e la visione a lungo termine.

## 1. Obiettivo

Alpilab AI è un assistente tecnico cloud-first per laboratori di riparazione smartphone.  
Deve funzionare da browser su PC, tablet e smartphone, e in futuro come PWA.

Non è un'app desktop-only. Non sostituisce Alpilab Check: lo affianca.

## 2. Separazione dei sistemi

```text
Alpilab Check  ──(futuro bridge API/file/HTTP)──►  Alpilab AI Cloud
      ▲                                              │
      │                                              ▼
Alpilab Hub (Windows PC) ◄──────────────────── Web / PWA clients
      │
      ├── software lab (3uTools, Borneo, ZXW, …)
      └── hardware (microscopio, termocamera, multimetro, alimentatore)
```

Regole:

- **Nessun import** del codice interno di Alpilab Check in questa repository.
- Check e AI condividono solo contratti dati stabili (schemi + connector).
- Hub è l'unico ponte verso processi/hardware del PC di laboratorio.

## 3. Layer logici

### Frontend (`frontend/`)

Web responsive + futura PWA. Non implementato nella fondazione.

### Backend (`app/`)

- `api/` — HTTP REST (FastAPI)
- `core/` — settings, security/permission gates
- `schemas/` — contratti dominio riparazione
- `models/` — persistenza futura (DB)
- `services/` — orchestration applicativa
- `integrations/` — connettori esterni (Check, …)

### AI Layer (`ai/`)

- `providers/` — `AIProvider` astratto + implementazioni
- `router.py` — selezione provider
- `prompts/` — prompt riutilizzabili
- `schemas.py` — request/response AI

Il codice applicativo parla solo con `AIRouter` / `AIService`, mai con SDK vendor.

### Knowledge (`knowledge/`)

Placeholder per manuals, boardview metadata, RAG e memoria soluzioni.

### Hub (`hub/`)

Interfacce e mock del servizio Windows futuro.  
**Non** esegue programmi, shell o remote control in questa fase.

## 4. AI Provider Abstraction

Interfaccia comune:

| Metodo | Ruolo |
|---|---|
| `name` | Identificativo provider |
| `is_available()` | Disponibilità runtime |
| `generate()` | Generazione testo |
| `generate_with_image()` | Input multimodale |
| `generate_stream()` | Streaming token/chunk |

Fase attuale: solo `MockProvider`.

Provider futuri (OpenAI, Anthropic, Google, locale) dovranno implementare la stessa interfaccia.

## 5. AI Router

Responsabilità:

1. Ricevere una richiesta normalizzata
2. Scegliere un provider
3. Restituire una risposta normalizzata

Hook previsti (non ancora logiche complesse):

- provider locale vs cloud
- fallback se il primario non è disponibile
- scelta per tipo richiesta / costo / capacità
- presenza di immagini
- preferenze esplicite del chiamante

## 6. Contratto dati riparazione

Schemi in `app/schemas/repair.py` (comuni a AI / futuro Check / futuro Hub):

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

Questi schemi sono il contratto concettuale. La persistenza DB arriverà in una fase successiva senza cambiare i nomi dei campi pubblici senza motivazione documentata.

## 7. Alpilab Check Bridge

`AlpilabCheckConnector` definisce operazioni come:

- `is_available()`
- `get_connected_device()`
- `get_diagnostics()`
- `push_session_reference()`

Transport futuro undecided (HTTP locale, file, socket, Hub relay).  
Implementazione attuale: `MockAlpilabCheckConnector`.

## 8. Alpilab Hub

Capability previste (mock only):

- `open_application` / `close_application` (con conferma obbligatoria)
- `capture_microscope`
- `capture_thermal_camera`
- `read_multimeter`
- `read_power_supply`
- `get_pc_status`

Vincoli di sicurezza:

- nessuna remote shell
- nessun comando OS arbitrario
- azioni rischiose → conferma esplicita (`app.core.security`)

## 9. Storage e database (futuro)

- Produzione: PostgreSQL
- Sviluppo locale: possibile SQLite
- Object storage / filesystem per foto, annotazioni, manuali, schemi, export diagnostici

Non cablati nella fondazione.

## 10. Cosa non fare in questa fase

Non implementare solo perché è nella visione:

- auth completa, billing, deploy cloud
- provider AI reali / API a pagamento
- RAG completo, voice, CV avanzata
- controllo hardware reale
- integrazioni 3uTools / Borneo / ZXW reali

## 11. Cambiamenti architetturali

Prima di alterare la separazione dei layer o i contratti pubblici, documentare il motivo in questo file o in un ADR dedicato sotto `docs/`.
