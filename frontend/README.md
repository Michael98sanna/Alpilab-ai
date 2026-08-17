# Frontend Alpilab AI — UI V0.1

Web application React + TypeScript + Vite per Alpilab AI.

## Stack

- React 18
- TypeScript
- Vite 6
- CSS Modules + design tokens
- Vitest + Testing Library

## Avvio

```bash
npm install
npm run dev
```

Apri http://localhost:5173

## Script

| Comando | Descrizione |
|---------|-------------|
| `npm run dev` | Dev server |
| `npm run build` | Production build |
| `npm run preview` | Preview build |
| `npm test` | Vitest |

## Struttura

```text
frontend/src/
├── components/
│   ├── core/       # AlpilabCore
│   ├── chat/       # MessageList, ChatInput
│   ├── repair/     # RepairBanner, DiagnosticPanel
│   ├── tools/      # ContextualToolBar
│   ├── session/    # AppHeader, SessionDevices
│   └── ui/         # Button
├── pages/          # HomePage
├── hooks/          # useRepairSession
├── mock/           # scenario + mock AI
├── api/            # future API client (not used in V0.1)
├── styles/         # tokens + global
└── types/
```

## Stato V0.1

- Mock data only — no real API, auth, WebSocket, voice, or hardware
- Navigabile: nuova riparazione, chat, diagnostica, strumenti, pausa/resume
- Responsive: mobile bottom sheet, desktop sidebar
- PWA-ready structure (no service worker yet)

## Design

Dark-first, minimal, functional colors. See `src/styles/tokens.css`.
