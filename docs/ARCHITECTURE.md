# Alpilab AI — Architecture

## Purpose

**Alpilab AI** is a cloud-first technical AI assistant for a smartphone repair lab.

It is a **separate project** from **Alpilab Check** (existing Windows bench app for device identification and diagnostics).

Alpilab AI will later communicate with Alpilab Check through a **stable API / bridge contract**, never by importing Check’s internal code.

## High-level architecture (target)

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
                       ZXW                Multimetro
                                          Alimentatore
```

## Layers (current foundation)

### Frontend
- Planned responsive web app / future PWA
- Placeholder only in this phase (`frontend/`)

### Backend (`app/`)
- FastAPI HTTP API
- Configuration via `.env`
- Repair-domain schemas (shared future contract)
- Services that call the AI layer without knowing the vendor
- Integration stubs (Alpilab Check connector)

### AI layer (`ai/`)
- `AIProvider` abstract interface
- `MockProvider` for offline development
- `AIRouter` selects a provider (mock today; local/cloud/fallback hooks prepared)
- Prompt placeholders
- Provider-agnostic request/response schemas

### Hub (`hub/`)
- Conceptual Windows bridge interfaces + mock
- Capabilities: open/close app, microscope, thermal, multimeter, PSU, PC status
- **No** real process control, **no** arbitrary shell, **no** remote shell

### Knowledge (`knowledge/`)
- Placeholder for future RAG / technical KB / lab solution memory

### Database / storage
- PostgreSQL planned for production
- SQLite acceptable for local development
- Not fully wired in this phase
- Future storage: photos, annotated images, manuals, schematics, diagnostic files

## AI provider principle

We do **not** train a new model. We orchestrate existing models behind one interface:

```text
AIProvider
  - name
  - is_available()
  - generate()
  - generate_with_image()
  - generate_stream()
```

The application must not know whether the answer came from a local model, OpenAI, Google, Anthropic, or another provider.

## Shared data contract (repair domain)

Defined in `app/schemas/repair.py`:

- Device
- RepairSession
- CustomerIssue
- DiagnosticTest
- Measurement
- Diagnosis
- RepairAction
- RepairResult
- ImageAttachment
- Note

These schemas are intended as the common language between Alpilab AI, Alpilab Check (via bridge), and Alpilab Hub.

## Security principles

- No API keys or passwords in the repository
- Secrets only via `.env` (git-ignored); `.env.example` documents names only
- No arbitrary command execution
- Future Hub hardware/software actions require permissions
- Potentially dangerous actions require explicit confirmation

## What is intentionally NOT implemented yet

- Full authentication
- Cloud deployment
- Real paid AI APIs
- Real OpenAI / Gemini / other provider SDKs
- Cloud database
- Real hardware control
- Real 3uTools / Borneo / ZXW control
- Voice / hands-free
- Advanced computer vision
- Full RAG

## Extension points

| Area | Extension point | Status |
|------|-----------------|--------|
| AI | New class implementing `AIProvider` | Ready |
| Routing | `AIRouter.select_provider` | Minimal + hooks |
| Check | `AlpilabCheckConnector` | Interface + mock |
| Hub | `AlpilabHub` | Interface + mock |
| KB | `knowledge/` package | Placeholder |
| Frontend | `frontend/` | Placeholder |
