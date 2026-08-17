# Alpilab PC Agent (V0.1 + V0.2)

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

V0.1 supported only `AGENT_TEST`. V0.2 adds the first real execution path: `demo.safe_test`.

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

## What V0.1 cannot do

- Open 3uTools, Borneo, ZXW
- Control hardware
- Connect to Alpilab Check
- Run shell commands
- Windows Service / installer / tray icon

## Tests

```bash
python3 -m pytest tests/test_tool_execution.py tests/test_agent_ws.py tests/test_pc_agent.py -v
```
