#Requires -Version 5.1
# Prepares the Flutter Android project on a machine WITH Flutter SDK.
# Does not download Flutter.

$ErrorActionPreference = "Stop"
$mobile = Join-Path (Split-Path -Parent $PSScriptRoot) "clients\alpilab_mobile"
Set-Location $mobile

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    Write-Host "Flutter SDK non trovato." -ForegroundColor Red
    Write-Host "Install: https://docs.flutter.dev/get-started/install/windows"
    Write-Host "Poi: flutter doctor"
    exit 1
}

flutter --version
flutter create --project-name alpilab_mobile --org ai.alpilab --platforms=android,ios .
flutter pub get

$overlay = Join-Path $mobile "android_overlay\AndroidManifest.xml"
$target = Join-Path $mobile "android\app\src\main\AndroidManifest.xml"
if ((Test-Path $overlay) -and (Test-Path $target)) {
    Write-Host "Unisci manualmente i permessi da android_overlay\AndroidManifest.xml in:" -ForegroundColor Yellow
    Write-Host $target
}

Write-Host "Build debug APK:" -ForegroundColor Cyan
Write-Host "  flutter build apk --debug"
Write-Host "Output: build\app\outputs\flutter-apk\app-debug.apk"
