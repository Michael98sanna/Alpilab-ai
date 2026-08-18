# Build ALPILAB AI.exe on Windows (repo root).
# Requires: pip install -r requirements.txt -r requirements-desktop.txt

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "PyInstaller non trovato. Installa: python -m pip install -r requirements-desktop.txt" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "frontend\dist\index.html")) {
    Write-Host "[1] Build UI (legacy frontend bundled into EXE)..." -ForegroundColor Yellow
    Push-Location frontend
    if (-not (Test-Path "node_modules")) { npm install }
    @"
VITE_APP_MODE=realtime
VITE_API_URL=http://127.0.0.1:8000
VITE_WS_URL=ws://127.0.0.1:8000
"@ | Set-Content -Path .env -Encoding ascii
    npm run build
    Pop-Location
}

Write-Host "[2] PyInstaller..." -ForegroundColor Yellow
pyinstaller --noconfirm --clean packaging\alpilab.spec
Write-Host "Output: dist\ALPILAB AI.exe" -ForegroundColor Green
Write-Host "Config utente: %USERPROFILE%\.alpilab\" -ForegroundColor Gray
