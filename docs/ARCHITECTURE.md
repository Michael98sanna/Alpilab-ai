# Architecture — ALPILAB AI

## Purpose

ALPILAB AI is a **cloud-first** technical assistant for a smartphone repair lab.
It is a **separate project** from Alpilab Check (Windows bench tool).

Future communication with Check / Hub / third-party tools must use stable
contracts (HTTP/API/file/local bridge) — never direct imports of Check internals.

## Long-term system view

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

## Layering (phase 1)

| Layer | Responsibility | Status |
|-------|----------------|--------|
| `frontend/` | Responsive web / future PWA | Placeholder |
| `app/api` | HTTP API (FastAPI) | Minimal health + AI ask |
| `app/services` | Application orchestration | AIService |
| `app/models` | Shared domain contracts | Defined (no DB) |
| `app/integrations` | External systems (Check, …) | Mock connector |
| `ai/` | Provider abstraction + router | MockProvider |
| `hub/` | Windows PC bridge | Interfaces + mock |
| `knowledge/` | Future RAG corpus | Placeholder |
| `tests/` | Automated checks | Initial suite |

## AI provider abstraction

All providers implement `AIProvider`:

- `name`
- `is_available()`
- `generate()`
- `generate_with_image()`
- `generate_stream()`

The rest of the application talks to `AIRouter` / `AIService` only.
No lock-in to a single vendor.

## Domain contracts

Shared conceptual models (future contract with Check/Hub):

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

## Security principles

1. No API keys or passwords in the repository
2. Secrets via `.env` (gitignored); `.env.example` documents names only
3. No arbitrary command execution / remote shell
4. Future Hub actions: permission checks + confirmation for dangerous ops
5. Mock / placeholder code must be clearly labeled (`is_mock`, `[MOCK]`)

## What is intentionally NOT implemented yet

- Real OpenAI / Anthropic / Google / local model providers
- Full auth / multi-tenant users
- PostgreSQL persistence and cloud deploy
- Real Hub hardware control
- Real Alpilab Check integration
- RAG / voice / advanced computer vision
- Paid APIs

## Extending the architecture

Before changing layering or introducing a vendor-specific dependency into
`app/` or domain models, document the reason in this file and keep provider
SDKs confined to `ai/providers/`.
