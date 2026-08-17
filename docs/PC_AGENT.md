# Alpilab PC Agent (V0.1 + V0.2 + V0.3)

The PC Agent is a local Windows process that connects Alpilab AI to the laboratory PC.

**V0.1 scope:** connected, registered, online, heartbeat, and `AGENT_TEST`.  
**V0.2 scope:** controlled tool execution via `TOOL_EXECUTE` — only registered, authorized tools.  
**No shell, subprocess, PowerShell, or arbitrary Windows commands.**

## Architecture

```text
                    ALPILAB AI
                         │
                    INTENT (future)
                         │
                     COMMAND
                         │
                  AUTHORIZATION
                         │
                   ToolRegistry
                         │
                   AgentGateway
                         │
              WebSocket /ws/agent/{session_id}
                         │
                         ▼
                  ALPILAB PC AGENT
                         │
                LocalToolDispatcher
                         │
                 Registered Tool
                         │
                      RESULT
```

V0.1 supported only `AGENT_TEST`. V0.2 adds `demo.safe_test`. V0.3 adds **WindowsAppTool** and `windows.3utools.open`.

## Requirements

- Python 3.10+
- Same dependencies as backend (`pip install -r requirements.txt`)
- Backend running locally or via tunnel

## Configuration

Copy `pc_agent/.env.example` and set:

| Variable | Default | Description |
|----------|---------|-------------|
| `ALPILAB_WS_URL` | `ws://127.0.0.1:8000` | Backend WebSocket base URL |
| `ALPILAB_SESSION_ID` | `repair-001` | Repair session to join |
| `ALPILAB_AGENT_NAME` | `ALPILAB-PC` | Display name |
| `ALPILAB_HEARTBEAT_INTERVAL` | `25` | Heartbeat seconds |
| `ALPILAB_RECONNECT_BASE_DELAY` | `1` | Reconnect backoff base |
| `ALPILAB_RECONNECT_MAX_DELAY` | `32` | Reconnect backoff cap |
| `ALPILAB_RECONNECT_MAX_ATTEMPTS` | `8` | Max reconnect tries |

## Identity

A persistent `agent_id` is stored in:

`~/.alpilab/agent_identity.json`

It uses a random UUID — not hostname or MAC address.

## Start on Windows

```powershell
cd path\to\Alpilab-ai
pip install -r requirements.txt

# Terminal 1 — backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — PC Agent
set ALPILAB_WS_URL=ws://127.0.0.1:8000
set ALPILAB_SESSION_ID=repair-001
python -m pc_agent
```

Expected console output:

```text
[ALPILAB-AGENT] Starting...
[ALPILAB-AGENT] Agent ID: agent-xxxxxxxxxxxx
[ALPILAB-AGENT] Connecting...
[ALPILAB-AGENT] Connected
[ALPILAB-AGENT] Registered
[ALPILAB-AGENT] ONLINE
```

## WebSocket protocol

### Connect

`ws://{host}/ws/agent/{session_id}?agent_id={agent_id}`

### Register (first message)

```json
{
  "type": "register",
  "agent_id": "...",
  "agent_name": "ALPILAB-PC",
  "platform": "windows",
  "agent_version": "0.2.0",
  "capabilities": {
    "safe_test": true,
    "windows_apps": false,
    "alpilab_check": false,
    "microscope": false,
    "thermal_camera": false,
    "multimeter": false,
    "power_supply": false
  },
  "status": "ONLINE"
}
```

Server responds: `{ "type": "registered", "message": "REGISTERED" }`

### Heartbeat

Client → `{ "type": "heartbeat" }`  
Server → `{ "type": "heartbeat_ack" }`

### AGENT_TEST command

Server → `{ "type": "command", "command": { "type": "AGENT_TEST", ... } }`  
Client → `{ "type": "agent_test_result", "success": true, ... }`

Trigger from REST:

`POST /api/v1/sessions/{session_id}/agents/{agent_id}/test`

### TOOL_EXECUTE command (V0.2)

Server → `{ "type": "command", "command": { "type": "TOOL_EXECUTE", ... } }`

```json
{
  "command_id": "...",
  "request_id": "...",
  "type": "TOOL_EXECUTE",
  "source": "alpilab_ai",
  "target": "agent-...",
  "timestamp": "...",
  "payload": {
    "tool_id": "demo.safe_test",
    "arguments": {}
  }
}
```

Client → `{ "type": "tool_execute_result", "success": true, "tool_id": "demo.safe_test", ... }`

```json
{
  "request_id": "...",
  "command_id": "...",
  "agent_id": "...",
  "tool_id": "demo.safe_test",
  "success": true,
  "result": {
    "status": "ok",
    "message": "Alpilab PC Agent tool execution works"
  },
  "error": null,
  "timestamp": "..."
}
```

Trigger from REST (validated, tool-specific — not a generic `/execute` endpoint):

`POST /api/v1/sessions/{session_id}/agents/{agent_id}/tools/demo.safe_test/execute`

List registered executable tools:

`GET /api/v1/tools`

## Security (V0.2)

- **Allowlist:** only `AGENT_TEST` and `TOOL_EXECUTE` are accepted by the PC Agent
- **LocalToolDispatcher:** resolves only pre-registered tools — no dynamic shell/cmd/powershell/python tools
- **Authorization:** server checks tool exists, enabled, risk level (LOW/SAFE auto), and agent capabilities
- **Argument validation:** strict schema per tool — extra keys rejected (`INVALID_ARGUMENTS`)
- **Idempotency:** duplicate `request_id` / `command_id` are not executed twice
- **Timeout:** server waits up to 30s for agent response
- **Audit events:** `TOOL_EXECUTION_STARTED`, `TOOL_EXECUTION_COMPLETED`, `TOOL_EXECUTE_RESULT`
- No `eval`, `exec`, `subprocess`, `os.system`, PowerShell, or shell execution
- Declared capabilities gate execution — `safe_test: true` required for `demo.safe_test`
- WebSocket has **no authentication** yet — not production-ready

## Realtime UI

When the agent is online, session clients receive:

- `AGENT_CONNECTED` / `AGENT_DISCONNECTED` / `AGENT_HEARTBEAT`
- `TOOL_EXECUTION_STARTED` / `TOOL_EXECUTION_COMPLETED` / `TOOL_EXECUTE_RESULT` (V0.2)
- Snapshot field `pc_agent`
- Header badge: **PC Agent ● ONLINE**

## What V0.2 cannot do

- Open 3uTools, Borneo, ZXW
- Control hardware (microscope, thermal camera, multimeter, power supply)
- Connect to Alpilab Check
- Run shell commands or arbitrary executables
- Accept unregistered or client-defined tools
- Auto-execute MEDIUM/HIGH/CRITICAL risk tools (confirmation flow not implemented)
- Conversation-driven tool dispatch (`ConversationCommandEngine` integration deferred)

## Manual test (V0.2)

```powershell
# Terminal 1 — backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — PC Agent V0.2
$env:ALPILAB_WS_URL="ws://127.0.0.1:8000"
$env:ALPILAB_SESSION_ID="repair-001"
$env:ALPILAB_CAP_SAFE_TEST="true"
python -m pc_agent
```

Expected agent log on SAFE_TEST:

```text
[ALPILAB-AGENT] Received TOOL_EXECUTE
[ALPILAB-AGENT] Received TOOL_EXECUTE tool=demo.safe_test
[ALPILAB-AGENT] TOOL_EXECUTE completed
```

Execute from another terminal (replace `{agent_id}`):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/sessions/repair-001/agents/{agent_id}/tools/demo.safe_test/execute"
```

Smartphone on the same RepairSession receives `TOOL_EXECUTE_RESULT` via the existing realtime WebSocket.

## PC Agent V0.3 — WindowsAppTool

### Architecture

```text
ALPILAB AI
    ↓
windows.3utools.open
    ↓
Authorization
    ↓
ToolRegistry (server — no local path)
    ↓
AgentGateway
    ↓
PC Agent
    ↓
LocalToolRegistry
    ↓
WindowsAppTool
    ↓
Local App Registry + trusted config
    ↓
DRY_RUN or execution
```

**Principle:** the server sends only `tool_id`. The PC Agent resolves the **local executable path** from trusted configuration. The server never sends `path`, `executable`, or shell commands.

### Tool ID

| Tool | ID |
|------|-----|
| Open 3uTools | `windows.3utools.open` |

Future: `windows.borneo.open`, `windows.zxw.open` — same `WindowsAppTool`, different local registration.

### Risk level

`windows.3utools.open` is classified **`CONFIRM_REQUIRED`** (launches external software). V0.3 auto-executes via dev/test endpoints until a confirmation UI exists.

### Local configuration

Copy `pc_agent/windows_apps.json.example` to `%USERPROFILE%\.alpilab\windows_apps.json` or use environment variables:

| Variable | Description |
|----------|-------------|
| `ALPILAB_CAP_WINDOWS_APPS` | Capability declaration (`true`) |
| `ALPILAB_WINAPP_3UTOOLS_ENABLED` | Enable 3uTools locally |
| `ALPILAB_WINAPP_3UTOOLS_PATH` | Full path to `3uTools.exe` on this PC |
| `ALPILAB_WINAPP_3UTOOLS_DRY_RUN` | `true` = validate only, do not launch |

Example `.env`:

```powershell
$env:ALPILAB_CAP_WINDOWS_APPS="true"
$env:ALPILAB_WINAPP_3UTOOLS_ENABLED="true"
$env:ALPILAB_WINAPP_3UTOOLS_PATH="C:\Program Files\3uTools\3uTools.exe"
$env:ALPILAB_WINAPP_3UTOOLS_DRY_RUN="true"
```

### DRY RUN result

```json
{
  "mode": "dry_run",
  "app_id": "3utools",
  "executable": "3uTools.exe",
  "validated": true,
  "would_execute": true
}
```

3uTools **must not** open when `dry_run=true`.

### Execution result

Set `ALPILAB_WINAPP_3UTOOLS_DRY_RUN=false` only after dry-run succeeds:

```json
{
  "mode": "execution",
  "app_id": "3utools",
  "started": true
}
```

Launch uses `subprocess.Popen([path], shell=False)` — never `shell=True`, PowerShell, or `cmd.exe`.

### REST dev endpoint

```text
POST /api/v1/sessions/{session_id}/agents/{agent_id}/tools/windows.3utools.open/execute
```

PowerShell:

```powershell
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/v1/sessions/repair-001/agents/$agentId/tools/windows.3utools.open/execute"
```

### Manual Windows test

**STEP 1** — Configure 3uTools path locally (`DRY_RUN=true`).

**STEP 2** — Start backend: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

**STEP 3** — (Optional) Start frontend on `?session=repair-001`

**STEP 4** — Start PC Agent with `windows_apps` capability and 3uTools config.

**STEP 5** — Verify PC Agent ● ONLINE.

**STEP 6** — Dry run: POST `windows.3utools.open` → `validated=true`, `would_execute=true`, 3uTools **does not open**.

**STEP 7** — Set `ALPILAB_WINAPP_3UTOOLS_DRY_RUN=false`, restart agent, POST again.

**STEP 8** — 3uTools opens → `started=true`.

### Error codes (V0.3)

| Code | Meaning |
|------|---------|
| `TOOL_NOT_FOUND` | Unknown tool_id |
| `TOOL_DISABLED` | Tool or app disabled locally |
| `CAPABILITY_MISSING` | Agent lacks `windows_apps` |
| `EXECUTABLE_NOT_FOUND` | Path missing or file not found |
| `INVALID_ARGUMENTS` | Remote args include forbidden keys (`path`, `executable`, …) |
| `APP_NOT_REGISTERED` | No local config for app |
| `AUTHORIZATION_DENIED` | Server authorization failed |

### Limitations (V0.3)

- No process lifecycle / PID management / close app
- No duplicate-instance detection (may start second 3uTools window)
- Borneo and ZXW not implemented yet
- No conversation text → tool mapping yet
- No remote path or arbitrary executable from server/client payload

## What V0.1 cannot do

- Open 3uTools, Borneo, ZXW
- Control hardware
- Connect to Alpilab Check
- Run shell commands
- Windows Service / installer / tray icon

## Tests

```bash
python3 -m pytest tests/test_tool_execution.py tests/test_windows_app_tool.py tests/test_agent_ws.py tests/test_pc_agent.py -v
```
