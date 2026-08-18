# Setup PC lavoro — copia e incolla in PowerShell (modifica percorso se serve)

## 0. Prerequisiti
# - Python 3.10+  → python --version
# - Node.js 18+   → node --version
# - Git             → git --version
# - 3uTools installato sul PC lavoro (per test reale)

## 1. Clone + branch
cd C:\Users\michael\Desktop
git clone https://github.com/Michael98sanna/Alpilab-ai.git
cd Alpilab-ai
git checkout cursor/pc-agent-v0-4
python -m pip install -r requirements.txt
cd frontend
npm install
cd ..

## 2. Trova IP PC lavoro
ipconfig
# Usa IPv4 di Wi-Fi o Ethernet (es. 192.168.1.55)

## 3. Terminale 1 — Backend
cd C:\Users\michael\Desktop\Alpilab-ai
$env:CORS_ORIGINS="http://<IP-PC>:5173"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

## 4. Terminale 2 — PC Agent
cd C:\Users\michael\Desktop\Alpilab-ai
$env:ALPILAB_WS_URL="ws://127.0.0.1:8000"
$env:ALPILAB_SESSION_ID="repair-001"
$env:ALPILAB_CAP_WINDOWS_APPS="true"
$env:ALPILAB_WINAPP_3UTOOLS_ENABLED="true"
$env:ALPILAB_WINAPP_3UTOOLS_PATH="C:\Program Files\3uTools9\3uTools.exe"
$env:ALPILAB_WINAPP_3UTOOLS_DRY_RUN="true"
python -m pc_agent

## 5. Terminale 3 — Frontend
cd C:\Users\michael\Desktop\Alpilab-ai\frontend
# Crea .env (sostituisci <IP-PC> — vedi anche frontend/realtime.env.example):
@"
VITE_APP_MODE=realtime
VITE_API_URL=http://<IP-PC>:8000
VITE_WS_URL=ws://<IP-PC>:8000
"@ | Set-Content -Path .env -Encoding UTF8
npm run dev -- --host 0.0.0.0

## 6. Smartphone (stessa Wi-Fi)
# http://<IP-PC>:5173/?session=repair-001

## 7. Test automatico (Terminale 4)
cd C:\Users\michael\Desktop\Alpilab-ai
.\scripts\quick_test_home.ps1

## 8. Test chat manuale
# Aprimi 3uTools          → apre 3uTools (dry_run=false) o messaggio dry-run
# Ho un iPhone...         → nessuna azione
# Apri Borneo             → non supportato

## Firewall (PowerShell Admin, se smartphone non apre)
# New-NetFirewallRule -DisplayName "Alpilab Frontend 5173" -Direction Inbound -Protocol TCP -LocalPort 5173 -Action Allow
# New-NetFirewallRule -DisplayName "Alpilab Backend 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
