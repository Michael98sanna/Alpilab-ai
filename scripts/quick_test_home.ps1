# Quick test — sostituisci IP o lascia auto-detect
# Esegui dalla root repo: .\scripts\quick_test_home.ps1

param(
    [string]$HostIP = "",
    [string]$Session = "repair-001"
)

if (-not $HostIP) {
    $HostIP = (
        Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object {
            $_.IPAddress -notlike "127.*" -and
            $_.IPAddress -notlike "169.254.*"
        } |
        Select-Object -First 1 -ExpandProperty IPAddress
    )
}

if (-not $HostIP) {
    Write-Host "Impossibile rilevare IP. Usa: .\scripts\quick_test_home.ps1 -HostIP 192.168.x.x" -ForegroundColor Red
    exit 1
}

Write-Host "=== ALPILAB V0.4 Quick Test ===" -ForegroundColor Cyan
Write-Host "PC IP: $HostIP | Session: $Session`n"

Write-Host "[1] Backend health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://${HostIP}:8000/health" -TimeoutSec 5
    Write-Host "    OK: $($health | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "    FAIL: backend non raggiungibile su http://${HostIP}:8000" -ForegroundColor Red
    Write-Host "    Avvia: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor Gray
    exit 1
}

Write-Host "`n[2] PC Agent status..." -ForegroundColor Yellow
try {
    $agents = Invoke-RestMethod -Uri "http://${HostIP}:8000/api/v1/sessions/${Session}/agents" -TimeoutSec 5
    if ($agents.agents.Count -eq 0) {
        Write-Host "    WARN: nessun agent — avvia PC Agent (Terminale 2)" -ForegroundColor Red
    } else {
        foreach ($a in $agents.agents) {
            $color = if ($a.status -eq "ONLINE") { "Green" } else { "Red" }
            Write-Host "    Agent $($a.agent_id): $($a.status)" -ForegroundColor $color
        }
    }
} catch {
    Write-Host "    WARN: agent status non disponibile ($($_.Exception.Message))" -ForegroundColor Red
}

Write-Host "`n[3] URL smartphone:" -ForegroundColor Yellow
Write-Host "    http://${HostIP}:5173/?session=${Session}" -ForegroundColor Cyan

Write-Host "`n[4] Test chat 'Aprimi 3uTools'..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Push-Location $repoRoot
python scripts/e2e_smartphone_chat.py --host $HostIP --session $Session
$code = $LASTEXITCODE
Pop-Location

if ($code -eq 0) {
    Write-Host "`n=== TEST OK ===" -ForegroundColor Green
} else {
    Write-Host "`n=== TEST FAIL ===" -ForegroundColor Red
}
exit $code
