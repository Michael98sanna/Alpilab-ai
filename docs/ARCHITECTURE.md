# Architettura Alpilab AI

Documento di riferimento per la visione a lungo termine e per i confini della fase fondazionale.

## 1. Posizionamento

**Alpilab AI** è un sistema **cloud-first** accessibile da browser su PC, smartphone e tablet (futura PWA). Non è un’applicazione desktop sostitutiva di Alpilab Check.

**Alpilab Check** resta un prodotto Windows autonomo usato al banco per identificazione e diagnostica. La comunicazione futura avviene solo tramite un **contratto dati/API** (`AlpilabCheckConnector`), senza importare moduli interni di Check.

## 2. Vista logica

```text
┌──────────────────────────────────────────────────────────┐
│                     Clienti                              │
│   Browser PC · Android · iOS · Tablet · (PWA futura)     │
└───────────────────────────┬──────────────────────────────┘
                            │ HTTPS
┌───────────────────────────▼──────────────────────────────┐
│                   ALPILAB AI CLOUD                       │
│  ┌─────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │ API     │  │ AI Router    │  │ Knowledge / RAG     │  │
│  │ Auth*   │──│ Providers*   │──│ Repair history*     │  │
│  │ Files*  │  │ Prompts      │  │ Docs / schemi*      │  │
│  └─────────┘  └──────────────┘  └─────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Database (PostgreSQL prod* / SQLite dev*)           │ │
│  │ Storage (foto, annotazioni, manuali*)               │ │
│  └─────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────┘
                            │ Bridge sicuro* (permessi + conferma)
┌───────────────────────────▼──────────────────────────────┐
│                   ALPILAB HUB* (Windows PC)              │
│  Allow-listed actions only — no arbitrary shell          │
│  Check · 3uTools* · Borneo* · ZXW*                       │
│  Microscopio* · Termocamera* · Multimetro* · PSU*        │
└──────────────────────────────────────────────────────────┘

* = pianificato / non implementato nella fondazione
```

## 3. Layer AI

### Contratto `AIProvider`

Ogni provider implementa:

- `name`
- `is_available()`
- `generate(request)`
- `generate_with_image(request)`
- `generate_stream(request)`

L’app usa solo `AIRouter`. Non conosce OpenAI, Gemini, modelli locali, ecc.

### Router (fondazione)

Oggi: provider configurato (default `MockProvider`), con lista `fallback_providers` pronta ma semplice.

Domani (non ora): scelta per tipo richiesta, costo, capacità, immagini, disponibilità, catene di fallback locali/cloud.

### Provider reali

Verranno aggiunti come moduli in `ai/providers/` che leggono chiavi da `.env`. **Mai** nel codice o nel git.

## 4. Contratto dati riparazione

I modelli in `app/models` sono il contratto concettuale condiviso tra AI, futuro Check bridge e Hub:

| Modello | Ruolo |
|--------|--------|
| `Device` | Dispositivo in riparazione |
| `CustomerIssue` | Problema segnalato |
| `RepairSession` | Aggregato sessione |
| `DiagnosticTest` | Test diagnostici |
| `Measurement` | Misure banco (V, A, Ω, °C, …) |
| `Diagnosis` | Diagnosi / ipotesi + confidenza |
| `RepairAction` | Azioni eseguite (con flag conferma) |
| `RepairResult` | Esito |
| `ImageAttachment` | Foto / annotazioni |
| `Note` | Note libere |

Persistenza DB completa: fase successiva. Gli schema restano il contratto.

## 5. Integrazioni

### Alpilab Check

`app/integrations/alpilab_check.py` definisce `AlpilabCheckConnector`.

- Nessun import da repository Check
- Nessuna ipotesi sul funzionamento interno
- Transport futuro: HTTP / file / local bridge — da definire quando servirà

### Alpilab Hub

`hub/` espone capacità esplicite:

- `open_application` / `close_application` (allow-list)
- `capture_microscope` / `capture_thermal_camera`
- `read_multimeter` / `read_power_supply`
- `get_pc_status`

**Vietato:** remote shell, comandi arbitrari, avvio processi reali in questa fase.

Azioni potenzialmente pericolose: `requires_confirmation` + permessi (futuro).

## 6. Frontend

`frontend/` è un placeholder. Target: web responsive + PWA installabile. Stack UI da scegliere in una fase dedicata; il backend espone già HTTP JSON.

## 7. Sicurezza (fin dall’inizio)

- Segreti solo in `.env` (gitignored)
- Nessuna API key nel repository
- Provider intercambiabili
- Hub: allow-list, no shell arbitraria
- Conferma esplicita per azioni rischiose (modello già previsto nei risultati Hub / `RepairAction`)

## 8. Cosa non fare in questa fase

Non aggiungere: auth completa, deploy cloud, SDK provider a pagamento, RAG completo, controllo hardware reale, integrazioni 3uTools/Borneo/ZXW reali, voce, CV avanzata.

## 9. Motivi di eventuali cambi architetturali

Prima di alterare la separazione `app` / `ai` / `hub` / `knowledge` / `frontend`, documentare qui:

- problema che emerge;
- alternative considerate;
- impatto su Check bridge e su Hub.

_(Nessun cambio rispetto al piano iniziale al momento della fondazione.)_
