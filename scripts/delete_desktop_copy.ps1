# Elimina Desktop\ALPILAB AI con file fantasma Defender (error 225).
# Uso: scripts\DELETE_DESKTOP_COPY.bat  (clicca SI su UAC)

param([switch]$ForceDelete)

$ErrorActionPreference = "Continue"
$Target = Join-Path $env:USERPROFILE "Desktop\ALPILAB AI"
$BlockedExe = Join-Path $Target "Releases\Windows\ALPILAB AI.exe"
$LogPath = Join-Path $env:TEMP "alpilab_delete_desktop.log"
$ExitCode = 0

function Write-Step([string]$Message, [string]$Color = "White") {
    Write-Host $Message -ForegroundColor $Color
    Add-Content -Path $LogPath -Value $Message -ErrorAction SilentlyContinue
}

function Wait-Exit {
    Write-Host ""
    Read-Host "Premi Invio per chiudere"
    exit $ExitCode
}

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-GhostExe {
    if (-not (Test-Path -LiteralPath $Target)) { return $false }
    $listed = Get-ChildItem -LiteralPath $Target -Recurse -Force -Filter "ALPILAB AI.exe" -ErrorAction SilentlyContinue
    if (-not $listed) { return $false }
    return -not (Test-Path -LiteralPath $listed[0].FullName)
}

function Invoke-DeleteMethods {
    param([string]$Path)

    Write-Step "  Metodo A: Remove-Item..." "Gray"
    try {
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
        if (-not (Test-Path -LiteralPath $Path)) { return $true }
    }
    catch {
        Write-Step "    Fallito: $($_.Exception.Message)" "DarkGray"
    }

    Write-Step "  Metodo B: cmd del / rd (percorso lungo)..." "Gray"
    try {
        Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue | ForEach-Object {
            $long = "\\?\$($_.FullName)"
            cmd /c "del /f /q `"$long`"" | Out-Null
        }
        $longRoot = "\\?\$Path"
        cmd /c "rd /s /q `"$longRoot`"" | Out-Null
        if (-not (Test-Path -LiteralPath $Path)) { return $true }
    }
    catch {
        Write-Step "    Fallito: $($_.Exception.Message)" "DarkGray"
    }

    Write-Step "  Metodo C: robocopy /purge (svuota cartella)..." "Gray"
    try {
        $empty = Join-Path $env:TEMP ("alpilab_empty_" + [guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Path $empty -Force | Out-Null
        cmd /c "robocopy `"$empty`" `"$Path`" /purge /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS" | Out-Null
        Remove-Item -LiteralPath $empty -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
        cmd /c "rd /s /q `"\\?\$Path`"" | Out-Null
        if (-not (Test-Path -LiteralPath $Path)) { return $true }
    }
    catch {
        Write-Step "    Fallito: $($_.Exception.Message)" "DarkGray"
    }

    return -not (Test-Path -LiteralPath $Path)
}

function Invoke-AdminCleanup {
    $rtpWasEnabled = $false
    try {
        Write-Step "[1] Esclusioni Windows Defender..." "Yellow"
        try {
            Add-MpPreference -ExclusionPath $Target -ErrorAction Stop
            Add-MpPreference -ExclusionPath $BlockedExe -ErrorAction SilentlyContinue
            Write-Step "     Esclusioni aggiunte." "Green"
        }
        catch {
            Write-Step "     Esclusioni: $($_.Exception.Message)" "Yellow"
        }

        Write-Step "[2] Disattivo protezione tempo reale (temporaneo)..." "Yellow"
        try {
            $status = Get-MpComputerStatus -ErrorAction Stop
            if ($status.RealTimeProtectionEnabled) {
                Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction Stop
                $rtpWasEnabled = $true
                Start-Sleep -Seconds 3
                Write-Step "     RTP OFF." "Green"
            }
        }
        catch {
            Write-Step "     RTP: $($_.Exception.Message)" "Yellow"
            Write-Step "     Se vedi 'Protezione against tampering', disattivala manualmente in Sicurezza di Windows." "Yellow"
        }

        Write-Step "[3] Tentativi eliminazione..." "Yellow"
        if (Invoke-DeleteMethods -Path $Target) {
            Write-Step "[OK] Cartella eliminata." "Green"
            return 0
        }

        Write-Step "[ERRORE] File fantasma ancora presente." "Red"
        return 1
    }
    finally {
        if ($rtpWasEnabled) {
            try { Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction Stop } catch {}
        }
    }
}

function Show-ManualSteps {
    Write-Step "" 
    Write-Step "PASSI MANUALI (importante - non basta l'esclusione):" "Yellow"
    Write-Step "  1. Sicurezza di Windows -> Protezione da virus e minacce" "White"
    Write-Step "  2. CRONOLOGIA PROTEZIONE (non Quarantena Acronis)" "White"
    Write-Step "  3. Cerca ALPILAB AI.exe -> Azioni -> CONSENTI/Elimina" "White"
    Write-Step "  4. Impostazioni -> Protezione anti-manomissione -> OFF (temporaneo)" "White"
    Write-Step "  5. Rilancia DELETE_DESKTOP_COPY.bat" "White"
    Write-Step "" 
    Write-Step "Se ancora bloccato: riavvia in MODALITA' SICURA (F8) ed elimina la cartella." "Yellow"
    Write-Step "Oppure ignorala: l'app funziona da Alpilab-ai\build\release\" "Gray"
}

"" | Set-Content -Path $LogPath -ErrorAction SilentlyContinue

Write-Host ""
Write-Step "=== Elimina Desktop\ALPILAB AI ===" "Cyan"
Write-Step "Target: $Target"
Write-Step "Log:  $LogPath"
if (Test-GhostExe) {
    Write-Step "Stato: file fantasma Defender rilevato" "Yellow"
}
Write-Host ""

if (-not $ForceDelete) {
    if (-not (Test-IsAdmin)) {
        Write-Step "Avvio con permessi admin (UAC)..." "Yellow"
        Write-Host ""
        try {
            $proc = Start-Process -FilePath "powershell.exe" -Verb RunAs -Wait -PassThru `
                -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PSCommandPath, "-ForceDelete")
            if ($null -eq $proc) {
                Write-Step "[ERRORE] UAC annullato." "Red"
                $ExitCode = 1
            }
            else {
                $ExitCode = $proc.ExitCode
            }
        }
        catch {
            Write-Step "[ERRORE] $($_.Exception.Message)" "Red"
            $ExitCode = 1
        }

        if ($ExitCode -ne 0 -or (Test-Path -LiteralPath $Target)) {
            Show-ManualSteps
        }
        Wait-Exit
    }
}

if (-not (Test-IsAdmin)) {
    Write-Step "[ERRORE] Servono permessi admin." "Red"
    $ExitCode = 1
    Wait-Exit
}

if (-not (Test-Path -LiteralPath $Target)) {
    Write-Step "[OK] Cartella gia' assente." "Green"
    Wait-Exit
}

$ExitCode = Invoke-AdminCleanup
if ($ExitCode -ne 0) {
    Show-ManualSteps
}
Wait-Exit
