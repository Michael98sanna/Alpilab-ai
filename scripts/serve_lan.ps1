# Serve UI + API sulla stessa porta 8000 (consigliato per smartphone).
# Esegui dalla root repo: .\scripts\serve_lan.ps1 -HostIP 192.168.0.41

param(
    [string]$HostIP = "192.168.0.41",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

Write-Host "=== ALPILAB LAN serve (porta unica $Port) ===" -ForegroundColor Cyan
Write-Host "IP: $HostIP`n"

$envContent = @"
VITE_APP_MODE=realtime
VITE_API_URL=http://${HostIP}:${Port}
VITE_WS_URL=ws://${HostIP}:${Port}
"@
Set-Content -Path (Join-Path $repo "frontend\.env") -Value $envContent -Encoding ascii

Write-Host "[1] Build frontend..." -ForegroundColor Yellow
Push-Location (Join-Path $repo "frontend")
npm run build
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    throw "npm run build fallito"
}
Pop-Location

$env:CORS_ORIGINS = "http://${HostIP}:${Port},http://${HostIP}:5173"
Write-Host "[2] Backend+UI su http://${HostIP}:${Port}/?session=repair-001" -ForegroundColor Green
Write-Host "    Smartphone: stessa URL sulla stessa Wi-Fi`n" -ForegroundColor Cyan
python -m uvicorn app.main:app --host 0.0.0.0 --port $Port
