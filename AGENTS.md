# AGENTS.md

## Cursor Cloud specific instructions

Alpilab AI is a Python **FastAPI + WebSocket** backend plus a **React + TypeScript + Vite** frontend. See `README.md` for the full architecture and feature history; this section only captures non-obvious cloud/dev caveats.

### Services

| Service | Dir | Run (dev) | URL |
|---------|-----|-----------|-----|
| Backend (FastAPI realtime) | `/workspace` | `python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | http://127.0.0.1:8000 |
| Frontend (Vite dev) | `frontend/` | `npm run dev -- --host 0.0.0.0` | http://127.0.0.1:5173 |
| CLI (MockProvider) | `/workspace` | `python3 app.py` | interactive stdin |

The update script already installs backend (`pip install -r requirements.txt`) and frontend (`npm install` in `frontend/`) dependencies on boot, so you normally just start the services above.

### Non-obvious caveats

- **Frontend REALTIME mode requires a `frontend/.env`.** It is gitignored and NOT created by the update script. Default `npm run dev` runs in MOCK mode (no backend). To exercise the WebSocket backend end-to-end, create `frontend/.env` from `frontend/.env.example` and set `VITE_APP_MODE=realtime`, `VITE_API_URL=http://127.0.0.1:8000`, `VITE_WS_URL=ws://127.0.0.1:8000`. Join a shared session via `http://localhost:5173/?session=repair-001`.
- **One backend test needs a built frontend.** `tests/test_v051_packaging.py::test_spec_paths_survive_packaging_cwd` asserts `frontend/dist/index.html` exists. Run `npm run build` in `frontend/` once before `python3 -m pytest tests/` or that single test fails (all others pass without a build). `frontend/dist/` is gitignored.
- **`tests/test_windows_app_tool.py::test_repair_session_audit_events` can be flaky** in the full-suite run (async `TOOL_EXECUTE_RESULT` broadcast timing). It passes reliably in isolation; re-run if it fails once — it is not a real regression.
- **Windows-desktop extras are optional and not needed here.** `requirements-desktop.txt` (`pywebview`, `pyinstaller`) is only for building the Windows EXE and is intentionally excluded from the update script. The pytest suite and Local Hub API do not require it.
- **No real AI keys / cloud services required.** Everything runs offline with `AI_PROVIDER=mock`. Backend `.env` is optional (copy from `.env.example`).

### Test / build commands

- Backend tests: `python3 -m pytest tests/` (194 tests; build the frontend first, see above).
- Frontend tests: `cd frontend && npm test` (Vitest, 50 tests).
- Frontend build: `cd frontend && npm run build` (runs `tsc --noEmit` typecheck + Vite build).
