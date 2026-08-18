# Build a desktop EXE (optional). Run from repo root on Windows.
# python -m pip install -r requirements-desktop.txt
# pyinstaller --noconfirm --name "ALPILAB AI" --windowed -m local_hub
# Output: dist\ALPILAB AI.exe

Write-Host "Install extras: python -m pip install -r requirements-desktop.txt"
Write-Host "Then: pyinstaller --noconfirm --name `"ALPILAB AI`" --windowed local_hub/__main__.py"
