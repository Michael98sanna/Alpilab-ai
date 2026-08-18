# Alpilab Local Hub + native clients (V0.5)

Local-first architecture: the laboratory PC is the source of truth. Cloud is optional.

## Goal

Double-click **ALPILAB AI** on Windows, or tap the Android app, and share one RepairSession on the LAN — no Chrome, no manual IP, no tunnel, no paid cloud.

```text
Windows App
  ├── Local Hub (FastAPI + SQLite + realtime)
  ├── PC Agent (V0.4 compatible)
  └── UI embedded (WebView, not Chrome)

Android / Tablet / iOS (Flutter)
  └── mDNS discovery → pairing → RepairSession
```

## Flutter

Flutter is **not installed** in the cloud agent environment and is **not auto-installed** (large toolchain). Client source lives in `clients/alpilab_mobile/`. Build APK on a machine with Flutter SDK.

## Start (Windows)

```powershell
cd Alpilab-ai
python -m pip install -r requirements.txt
python -m pip install -r requirements-desktop.txt   # pywebview (UI nativa)
python -m local_hub
```

Or double-click `clients\windows\Avvia ALPILAB AI.bat`

This starts:

1. FastAPI on `0.0.0.0:8000`
2. SQLite at `data/alpilab.db`
3. mDNS `_alpilab._tcp` as **Alpilab Negozio**
4. PC Agent subprocess (unless `--no-agent`)
5. Embedded window via **pywebview** (not Chrome)

Hub-only (no window):

```powershell
python -m local_hub --no-ui
```

## Manual tests

### Windows

1. `python -m local_hub`
2. Local Hub listening; desktop window opens
3. PC Agent ONLINE
4. Session `repair-001` (no `?session=` required)
5. Send `Ciao` → local mock reply
6. Send `Aprimi 3uTools` → V0.4 pipeline → 3uTools (if configured)

### Android

1. Install Flutter app (`clients/alpilab_mobile`)
2. Open → automatic search for Alpilab Negozio
3. On PC: **Collega dispositivo** → 6-digit code
4. Enter code on phone → authorized
5. Shared RepairSession
6. `Aprimi 3uTools` from phone → PC opens 3uTools

### Multi-device

Windows message appears on Android and vice versa (existing realtime).

### Offline

Disable Internet, keep Wi-Fi/LAN. Repeat chat + `Aprimi 3uTools`. Remote AI may be unavailable; MockProvider works.

## Pairing API

| Method | Path |
|--------|------|
| GET | `/api/v1/hub/info` |
| POST | `/api/v1/pairing/start` |
| POST | `/api/v1/pairing/complete` |
| GET | `/api/v1/pairing/clients` |
| DELETE | `/api/v1/pairing/clients/{client_id}` |

## Security

User text still never becomes a path/shell command. Natural language → `OPEN_APPLICATION` → `windows.3utools.open` only.

## Cost

Zero required cloud spend. Optional local LLM via `ALPILAB_LOCAL_AI_URL` (not downloaded automatically).

## Legacy web

`frontend/` remains as **legacy-dev-web** (UI V0.3.1). Product entrypoint is Local Hub + native wrappers.
