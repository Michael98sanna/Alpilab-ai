# Frontend Alpilab AI

Placeholder per la futura web application responsive e PWA.

## Struttura

```text
frontend/
├── public/
│   └── index.html          # Shell HTML (responsive, mobile/tablet/PC)
├── src/
│   ├── api/
│   │   └── client.js       # Client API stub
│   ├── styles/
│   │   └── base.css        # Stili base responsive
│   └── main.js             # Entry point
└── README.md
```

## Stato attuale

- Nessun bundler o framework installato (Vite/React/Vue in fase successiva)
- `AlpilabApiClient` predisposto per `/health` e `/api/v1/ai/generate`
- Layout responsive con viewport mobile-first
- PWA manifest e service worker: non implementati

## Prossimi passi

- Scelta stack UI (es. Vite + framework)
- Routing, autenticazione, stato applicazione
- PWA installabile su smartphone e tablet
- Integrazione con backend HTTP reale
