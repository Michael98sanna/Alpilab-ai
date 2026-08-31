# Ripristina ALPILAB AI quando un antivirus blocca l'EXE PyInstaller.
# Doppio click su FIX_DEFENDER_E_RICOMPILA.bat oppure tasto destro -> Esegui come amministratore.

$ErrorActionPreference = "Stop"
$LogPath = Join-Path $env:TEMP "alpilab_fix_defender.log"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$DistDir = Join-Path $RepoRoot "dist"
$DistExe = Join-Path $DistDir "ALPILAB AI.exe"
$DesktopRelease = Join-Path $env:USERPROFILE "Desktop\ALPILAB AI"

function Write-Step {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
    Add-Content -Path $LogPath -Value $Message
}

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Remove-BlockedPath {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Step "     (assente) $Path" "Gray"
        return $true
    }
    try {
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
        Write-Step "[OK] Rimosso: $Path" "Green"
        return $true
    }
    catch {
        Write-Step "[WARN] Impossibile rimuovere $Path" "Yellow"
        Write-Step "       $($_.Exception.Message)" "Yellow"
        return $false
    }
}

function Get-AntivirusProducts {
    try {
        return Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction Stop
    }
    catch {
        return @()
    }
}

function Enable-DefenderIfPossible {
    Write-Step "[1a] Stato Windows Defender..." "Yellow"
    $defender = Get-Service WinDefend -ErrorAction SilentlyContinue
    if ($null -eq $defender) {
        Write-Step "     Servizio WinDefend non presente" "Gray"
        return $false
    }
    Write-Step "     WinDefend: $($defender.Status) ($($defender.StartType))" "Gray"
    if ($defender.Status -ne "Running") {
        try {
            Set-Service WinDefend -StartupType Manual -ErrorAction SilentlyContinue
            Start-Service WinDefend -ErrorAction Stop
            Start-Service WdNisSvc -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            Write-Step "     WinDefend avviato" "Green"
            return $true
        }
        catch {
            Write-Step "     Impossibile avviare WinDefend: $($_.Exception.Message)" "Yellow"
            return $false
        }
    }
    return $true
}

function Add-DefenderExclusions {
    param([bool]$DefenderRunning)
    Write-Step "[1b] Esclusioni Windows Defender..." "Yellow"
    if (-not $DefenderRunning) {
        Write-Step "     Defender non attivo - salto esclusioni automatiche" "Yellow"
        return $false
    }
    try {
        Add-MpPreference -ExclusionPath $RepoRoot -ErrorAction Stop
        Add-MpPreference -ExclusionPath $DistDir -ErrorAction Stop
        Write-Step "     Esclusioni aggiunte per repo e dist" "Green"
        return $true
    }
    catch {
        Write-Step "     Esclusioni non disponibili: $($_.Exception.Message)" "Yellow"
        return $false
    }
}

function Show-ThirdPartyAvHint {
    $products = Get-AntivirusProducts | Where-Object { $_.displayName -notmatch '^Windows Defender$' }
    if (-not $products) { return }
    Write-Step "" 
    Write-Step "ATTENZIONE: antivirus di terze parti rilevato:" "Yellow"
    foreach ($p in $products) {
        Write-Step "  - $($p.displayName)" "Yellow"
    }
    Write-Step "Aggiungi esclusione manuale per:" "Yellow"
    Write-Step "  $RepoRoot" "White"
    Write-Step "Poi ripristina/rimuovi ALPILAB AI.exe dalla quarantena dell'antivirus." "Yellow"
}

if (-not (Test-IsAdmin)) {
    Write-Host ""
    Write-Host "Richiedo permessi amministratore (UAC)..." -ForegroundColor Yellow
    Write-Host "Clicca SI nella finestra che compare." -ForegroundColor Yellow
    Write-Host ""
    $argList = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $proc = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $argList -PassThru -Wait
    if ($null -eq $proc) {
        Write-Host "UAC annullato. Riprova e clicca SI." -ForegroundColor Red
        Read-Host "Premi Invio per chiudere"
        exit 1
    }
    exit $proc.ExitCode
}

"" | Set-Content -Path $LogPath
Write-Step ""
Write-Step "=== ALPILAB - Fix antivirus + rebuild ===" "Cyan"
Write-Step "Repo: $RepoRoot"
Write-Step "Log:  $LogPath"
Write-Step ""

$exitCode = 0
try {
    $defenderRunning = Enable-DefenderIfPossible
    $null = Add-DefenderExclusions -DefenderRunning $defenderRunning
    Show-ThirdPartyAvHint

    Write-Step "[2] Minacce ALPILAB in cronologia Defender..." "Yellow"
    if ($defenderRunning) {
        try {
            $threats = Get-MpThreatDetection -ErrorAction SilentlyContinue |
                Where-Object { $_.Resources -match 'ALPILAB|Alpilab-ai' }
            if ($threats) {
                $threats | ForEach-Object { Write-Step "     Threat: $($_.Resources)" "Gray" }
                Write-Step "     Ripristina queste voci da Sicurezza di Windows -> Cronologia protezione" "Yellow"
            }
            else {
                Write-Step "     Nessuna voce ALPILAB in cronologia Defender" "Gray"
            }
        }
        catch {
            Write-Step "     Cronologia Defender non disponibile" "Gray"
        }
    }
    else {
        Write-Step "     Defender non attivo" "Gray"
    }

    Write-Step "[3] Pulizia copia Desktop obsoleta..." "Yellow"
    $null = Remove-BlockedPath -Path $DesktopRelease

    Write-Step "[4] Pulizia EXE bloccato in dist..." "Yellow"
    $distRemoved = Remove-BlockedPath -Path $DistExe
    if (-not (Test-Path -LiteralPath $DistDir)) {
        New-Item -ItemType Directory -Path $DistDir | Out-Null
    }

    Write-Step "[5] Prossimo passo: BUILD (senza admin)" "Yellow"
    Write-Step "     Chiudi questa finestra." "White"
    Write-Step "     Doppio click su: scripts\BUILD_EXE.bat" "White"
    Write-Step "     (NON usare 'Esegui come amministratore')" "White"
    Write-Step ""
    if (-not $distRemoved) {
        Write-Step "PRIMA della build, in Acronis:" "Yellow"
        Write-Step "  - Esclusioni -> $RepoRoot" "White"
        Write-Step "  - Quarantena -> ripristina ALPILAB AI.exe" "White"
        Write-Step ""
    }
    else {
        Write-Step "[OK] Pulizia completata. Ora lancia BUILD_EXE.bat" "Green"
        Write-Step ""
    }
}
catch {
    Write-Step ""
    Write-Step "[ERRORE] $($_.Exception.Message)" "Red"
    Write-Step "" 
    Write-Step "Se Acronis True Image e' attivo:" "Yellow"
    Write-Step "  1. Apri Acronis -> Protezione attiva / Active Protection" "White"
    Write-Step "  2. Elenco esclusioni -> Aggiungi cartella:" "White"
    Write-Step "     $RepoRoot" "White"
    Write-Step "  3. Quarantena -> ripristina ALPILAB AI.exe se presente" "White"
    Write-Step "  4. Chiudi questa finestra e lancia scripts\BUILD_EXE.bat" "White"
    Write-Step ""
    Write-Step "Alternativa immediata (senza EXE):" "Yellow"
    Write-Step "  cd $RepoRoot" "White"
    Write-Step "  .\scripts\run_local_hub.ps1" "White"
    Write-Step ""
    Write-Step "Log completo: $LogPath" "Gray"
    Write-Step ""
    $exitCode = 1
}

Read-Host "Premi Invio per chiudere"
exit $exitCode
