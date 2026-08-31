@echo off
setlocal
cd /d "%~dp0.."
echo.
echo === ALPILAB - Elimina Desktop\ALPILAB AI ===
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0delete_desktop_copy.ps1"
set ERR=%ERRORLEVEL%
echo.
if %ERR% NEQ 0 (
    echo Operazione non riuscita. Controlla il messaggio sopra o il log in %%TEMP%%\alpilab_delete_desktop.log
) else (
    echo Operazione completata.
)
echo.
pause
exit /b %ERR%
