# Run Local Hub from repo root
Set-Location (Split-Path -Parent $PSScriptRoot)
python -m local_hub @args
