# run_all_full_baselines.ps1
# Master script to run all full baseline experiments for P0 paper using PowerShell.
# Usage: .\scripts\run_all_full_baselines.ps1 [--fallback-akt] [--overwrite]

$env:PYTHONPATH="."

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🌟 Starting MASTER PIPELINE for Reproducible KT baseline experiments" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# Run assist2012
.\scripts\run_full_assist2012_baselines.ps1 $args

# Run junyi
.\scripts\run_full_junyi_baselines.ps1 $args

# Run xes3g5m
.\scripts\run_full_xes3g5m_baselines.ps1 $args

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🎉 MASTER PIPELINE completed successfully for all datasets!" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
