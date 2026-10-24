# Rebuild frozen Appendix tables from summaries. Does not retrain.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONPATH = "."
python scripts/p0_rebuild_locked_tables.py
Write-Host "Frozen-table rebuild complete. Retrain path remains scripts/reproduce_one_dataset.ps1"
