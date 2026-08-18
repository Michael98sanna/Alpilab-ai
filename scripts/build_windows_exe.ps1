# Build ALPILAB AI.exe on Windows (repo root).
# Requires: pip install -r requirements.txt -r requirements-desktop.txt

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

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
# python -m so Scripts\ need not be on PATH. --distpath/--workpath keep output
# at repo root even though the spec lives under packaging\.
python -m PyInstaller --noconfirm --clean `
    --distpath (Join-Path $RepoRoot "dist") `
    --workpath (Join-Path $RepoRoot "build") `
    (Join-Path $RepoRoot "packaging\alpilab.spec")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$exe = Join-Path $RepoRoot "dist\ALPILAB AI.exe"
if (-not (Test-Path $exe)) {
    Write-Host "Build failed: $exe not found" -ForegroundColor Red
    exit 1
}
$info = Get-Item $exe
Write-Host "Output: $($info.FullName)" -ForegroundColor Green
Write-Host ("Size: {0:N0} bytes" -f $info.Length)
Write-Host "Timestamp: $($info.LastWriteTime)"
Write-Host "Config utente: %USERPROFILE%\.alpilab\" -ForegroundColor Gray
