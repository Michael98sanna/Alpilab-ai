#Requires -RunAsAdministrator
# Apre porte Alpilab su TUTTI i profili firewall (Domain/Private/Public).
# Esegui: clic destro PowerShell → Esegui come amministratore → .\scripts\open_firewall.ps1

$ErrorActionPreference = "Stop"

foreach ($port in 5173, 8000) {
    $name = "Alpilab port $port"
    Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -DisplayName $name -Direction Inbound -Protocol TCP -LocalPort $port -Action Allow -Profile Domain,Private,Public | Out-Null
    Write-Host "[OK] Porta $port aperta (Domain/Private/Public)" -ForegroundColor Green
}

$node = (Get-Command node -ErrorAction SilentlyContinue).Source
if ($node) {
    $name = "Alpilab Node.js inbound"
    Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -DisplayName $name -Direction Inbound -Program $node -Action Allow -Profile Domain,Private,Public | Out-Null
    Write-Host "[OK] Node.js permesso: $node" -ForegroundColor Green
}

Write-Host "`nTest dal telefono: http://192.168.0.41:8000/health" -ForegroundColor Cyan
