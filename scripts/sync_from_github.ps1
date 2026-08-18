#Requires -Version 5.1
<#
.SYNOPSIS
  Allinea TUTTA la cartella del repo a GitHub (file tracciati).

  Non tocca %USERPROFILE%\.alpilab\ (config, DB, log).
  Non cancella .venv, node_modules, dist (file non in git).

.USAGE
  Doppio click su "Aggiorna da GitHub.bat"
  oppure: .\scripts\sync_from_github.ps1
#>

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Branch = "cursor/native-local-v0-5-1"
$RepoUrl = "https://github.com/Michael98sanna/Alpilab-ai.git"

Set-Location $RepoRoot

Write-Host ""
Write-Host "=== ALPILAB — Aggiorna cartella da GitHub ===" -ForegroundColor Cyan
Write-Host "Cartella: $RepoRoot"
Write-Host "Branch:   $Branch"
Write-Host "Remote:   $RepoUrl"
Write-Host ""

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git non trovato. Installa: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

$inside = git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0 -or $inside -ne "true") {
    Write-Host "Questa cartella non e' un repo Git." -ForegroundColor Red
    Write-Host "Clona prima: gh repo clone Michael98sanna/Alpilab-ai" -ForegroundColor Yellow
    exit 1
}

git remote set-url origin $RepoUrl
Write-Host "[1] fetch origin..." -ForegroundColor Yellow
git fetch origin
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2] checkout $Branch..." -ForegroundColor Yellow
git checkout $Branch
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3] reset --hard origin/$Branch  (intera cartella = GitHub)..." -ForegroundColor Yellow
git reset --hard "origin/$Branch"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$head = git log -1 --oneline
Write-Host ""
Write-Host "[OK] Cartella allineata a GitHub" -ForegroundColor Green
Write-Host "HEAD: $head" -ForegroundColor Green
Write-Host "Dati utente: $env:USERPROFILE\.alpilab\" -ForegroundColor Gray
Write-Host ""
Write-Host "Poi, per il test EXE:" -ForegroundColor Cyan
Write-Host "  .\scripts\build_windows_exe.ps1" -ForegroundColor White
Write-Host "  doppio click su dist\ALPILAB AI.exe" -ForegroundColor White
Write-Host ""
