@echo off
setlocal
cd /d "%~dp0.."
echo.
echo === ALPILAB - Fix Defender e rebuild ===
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0fix_windows_defender.ps1"
exit /b %ERRORLEVEL%
