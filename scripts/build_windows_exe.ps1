# Build ALPILAB AI.exe on Windows (repo root).
# Output canonico: build\release\ALPILAB AI.exe (elimina la build precedente).
# Requires: pip install -r requirements.txt -r requirements-desktop.txt

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Resolve-AlpilabPython {
    $candidates = @(
        (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
        (Get-Command py -ErrorAction SilentlyContinue | ForEach-Object { & py -3 -c "import sys; print(sys.executable)" 2>$null }),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"),
        (Join-Path $env:ProgramFiles "Python312\python.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Python312\python.exe")
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique

    foreach ($candidate in $candidates) {
        try {
            $version = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $version) {
                Write-Host "Python: $candidate ($version)" -ForegroundColor Gray
                return $candidate
            }
        }
        catch {
            continue
        }
    }

    throw "Python non trovato. Installa Python 3.12 o aggiungilo al PATH."
}

$PythonExe = Resolve-AlpilabPython
$ReleaseDir = Join-Path $RepoRoot "build\release"
$ReleaseExe = Join-Path $ReleaseDir "ALPILAB AI.exe"

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Prepare-ReleaseDir {
    New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
    $probe = Join-Path $ReleaseDir ".write_probe"
    try {
        [System.IO.File]::WriteAllText($probe, "ok")
        Remove-Item -LiteralPath $probe -Force
    }
    catch {
        Write-Host ""
        Write-Host "[ERRORE] Impossibile scrivere in build\release\." -ForegroundColor Red
        Write-Host "Aggiungi esclusione antivirus per: $RepoRoot" -ForegroundColor Yellow
        exit 1
    }
}

function Remove-PreviousRelease {
    if (-not (Test-Path -LiteralPath $ReleaseExe)) {
        return
    }
    Write-Host "[0] Rimuovo build precedente..." -ForegroundColor Yellow
    try {
        Remove-Item -LiteralPath $ReleaseExe -Force -ErrorAction Stop
        Write-Host "     Rimossa: $ReleaseExe" -ForegroundColor Gray
    }
    catch {
        Write-Host ""
        Write-Host "[ERRORE] Impossibile rimuovere la build precedente." -ForegroundColor Red
        Write-Host "         $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Aggiungi esclusione antivirus per: $RepoRoot" -ForegroundColor Yellow
        exit 1
    }
}

if (Test-IsAdmin) {
    Write-Host ""
    Write-Host "ATTENZIONE: non eseguire la build come amministratore." -ForegroundColor Yellow
    Write-Host "Chiudi questa finestra e usa doppio click su scripts\BUILD_EXE.bat" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Prepare-ReleaseDir
Remove-PreviousRelease

Write-Host "[1] Build UI (always, so EXE is not stuck with a stale VITE_WS_URL)..." -ForegroundColor Yellow
Push-Location frontend
npm install
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
$env:VITE_APP_MODE = "realtime"
$env:VITE_API_URL = "http://127.0.0.1:8000"
$env:VITE_WS_URL = "ws://127.0.0.1:8000"
npx vite build
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
Pop-Location

Write-Host "[2] PyInstaller..." -ForegroundColor Yellow
& $PythonExe -m PyInstaller --noconfirm --clean `
    --distpath $ReleaseDir `
    --workpath (Join-Path $RepoRoot "build") `
    (Join-Path $RepoRoot "packaging\alpilab.spec")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path -LiteralPath $ReleaseExe)) {
    Write-Host "Build failed: $ReleaseExe not found" -ForegroundColor Red
    exit 1
}

$info = Get-Item -LiteralPath $ReleaseExe
Write-Host "Output: $($info.FullName)" -ForegroundColor Green
Write-Host ("Size: {0:N0} bytes" -f $info.Length)
Write-Host "Timestamp: $($info.LastWriteTime)"
Write-Host "Avvia: build\release\ALPILAB AI.exe" -ForegroundColor Cyan
Write-Host "Config utente: %USERPROFILE%\.alpilab\" -ForegroundColor Gray
