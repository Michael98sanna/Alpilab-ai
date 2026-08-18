#Requires -Version 5.1
<#
.SYNOPSIS
  Configura Git/GitHub su Windows (PC casa o lavoro).
.USAGE
  .\scripts\setup_git_windows.ps1
#>

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/Michael98sanna/Alpilab-ai.git"
$Branch = "main"

Write-Host "`n=== ALPILAB — Setup GitHub Windows ===" -ForegroundColor Cyan

function Test-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

# 1. Git
if (-not (Test-Command git)) {
    Write-Host "Git non trovato. Installa: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] git $(git --version)" -ForegroundColor Green

# 2. Git config base
git config --global init.defaultBranch main 2>$null
git config --global core.autocrlf true 2>$null
git config --global pull.rebase false 2>$null
git config --global credential.helper manager 2>$null
Write-Host "[OK] Git config base applicata" -ForegroundColor Green

# 3. GitHub CLI
if (-not (Test-Command gh)) {
    Write-Host "`nGitHub CLI (gh) non trovato." -ForegroundColor Yellow
    Write-Host "Installa: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host "Poi esegui: gh auth login" -ForegroundColor Yellow
    Write-Host "`nOppure usa SSH — vedi docs/GIT_SETUP.md" -ForegroundColor Yellow
    exit 0
}
Write-Host "[OK] gh $(gh --version | Select-Object -First 1)" -ForegroundColor Green

# 4. Auth status
Write-Host "`n--- Stato autenticazione ---" -ForegroundColor Yellow
$authOk = $true
try {
    gh auth status 2>&1 | ForEach-Object { Write-Host $_ }
} catch {
    $authOk = $false
}

if (-not $authOk) {
    Write-Host "`nNon autenticato. Esegui:" -ForegroundColor Yellow
    Write-Host "  gh auth login" -ForegroundColor Cyan
    Write-Host "Scegli: GitHub.com → HTTPS → Login with browser → Yes per Git credentials" -ForegroundColor Gray
    exit 1
}

# 5. Test accesso repo
Write-Host "`n--- Test accesso repo ---" -ForegroundColor Yellow
try {
    $head = git ls-remote $RepoUrl HEAD 2>&1
    if ($LASTEXITCODE -ne 0) { throw $head }
    Write-Host "[OK] Accesso repo: $RepoUrl" -ForegroundColor Green
    Write-Host "     HEAD: $($head.Split("`t")[0])" -ForegroundColor Gray
} catch {
    Write-Host "[FAIL] Impossibile accedere al repo" -ForegroundColor Red
    Write-Host "Pulisci credenziali vecchie:" -ForegroundColor Yellow
    Write-Host '  cmdkey /delete:LegacyGeneric:target=git:https://github.com' -ForegroundColor Cyan
    Write-Host "Poi: gh auth login" -ForegroundColor Cyan
    exit 1
}

# 6. Se siamo dentro il repo, correggi remote
$gitDir = git rev-parse --show-toplevel 2>$null
if ($gitDir) {
    Write-Host "`n--- Repo locale: $gitDir ---" -ForegroundColor Yellow
    git remote set-url origin $RepoUrl
    Write-Host "[OK] Remote origin impostato (senza token nell'URL)" -ForegroundColor Green
    git fetch origin 2>&1 | ForEach-Object { Write-Host $_ }
    git checkout $Branch 2>$null
    git reset --hard "origin/$Branch"
    Write-Host "[OK] Cartella allineata a origin/$Branch" -ForegroundColor Green
    Write-Host "`nUltimo commit:" -ForegroundColor Gray
    git log -1 --oneline
} else {
    Write-Host "`nNon sei in un repo Git." -ForegroundColor Yellow
    Write-Host "Per clonare:" -ForegroundColor Yellow
    Write-Host "  cd `$env:USERPROFILE\Desktop" -ForegroundColor Cyan
    Write-Host "  gh repo clone Michael98sanna/Alpilab-ai" -ForegroundColor Cyan
    Write-Host "  cd Alpilab-ai" -ForegroundColor Cyan
    Write-Host "  git checkout $Branch" -ForegroundColor Cyan
}

Write-Host "`n=== Setup completato ===" -ForegroundColor Green
Write-Host "Documentazione: docs/GIT_SETUP.md" -ForegroundColor Gray
Write-Host "Test app: scripts/SETUP_PC_LAVORO.md`n" -ForegroundColor Gray
