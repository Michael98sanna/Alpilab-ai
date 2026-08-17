# Alpilab PC Agent V0.1

The PC Agent is a local Windows process that connects Alpilab AI to the laboratory PC.

**V0.1 scope:** connected, registered, online, heartbeat, and `AGENT_TEST` only.  
**No real Windows commands are executed in this version.**

## Architecture

```text
                    ALPILAB AI
                         │
                  RepairSession
                         │
                   AgentGateway
                         │
              WebSocket /ws/agent/{session_id}
                         │
                         ▼
                  ALPILAB PC AGENT
                         │
                  AGENT_TEST ONLY
```

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
  "agent_version": "0.1.0",
  "capabilities": {
    "windows_apps": true,
    "alpilab_check": true,
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

## Security (V0.1)

- **Allowlist:** only `AGENT_TEST` is accepted by the PC Agent
- Any other command type returns `COMMAND_NOT_ALLOWED`
- No `subprocess`, `os.system`, PowerShell, or shell execution
- Declared capabilities are **not** execution permissions
- WebSocket has **no authentication** yet — not production-ready

## Realtime UI

When the agent is online, session clients receive:

- `AGENT_CONNECTED` / `AGENT_DISCONNECTED` / `AGENT_HEARTBEAT`
- Snapshot field `pc_agent`
- Header badge: **PC Agent ● ONLINE**

## What V0.1 cannot do

- Open 3uTools, Borneo, ZXW
- Control hardware
- Connect to Alpilab Check
- Run shell commands
- Windows Service / installer / tray icon

## Tests

```bash
python3 -m pytest tests/test_agent_ws.py tests/test_pc_agent.py -v
```
