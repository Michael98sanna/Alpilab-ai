@echo off
REM Allinea l'intera cartella del progetto al branch su GitHub.
REM I dati in %USERPROFILE%\.alpilab restano al loro posto.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\sync_from_github.ps1"
if errorlevel 1 (
  echo.
  echo Aggiornamento non riuscito. Se chiede login: gh auth login
  pause
  exit /b 1
)
pause
