@echo off
setlocal
cd /d "%~dp0.."
echo.
echo === ALPILAB - Build EXE (senza admin) ===
echo Output: build\release\ALPILAB AI.exe
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows_exe.ps1"
set ERR=%ERRORLEVEL%
echo.
if %ERR% NEQ 0 (
    echo Build fallita. Controlla il messaggio sopra.
) else (
    echo [OK] Avvia: build\release\ALPILAB AI.exe
)
echo.
pause
exit /b %ERR%
