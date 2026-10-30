# run_full_xes3g5m_baselines.ps1
# Run full XES3G5M baseline experiments for seeds 2024 and 2025 (learner_based split).
# Usage: .\scripts\run_full_xes3g5m_baselines.ps1 [--fallback-akt] [--overwrite]

$env:PYTHONPATH="."

Write-Host "=========================================================" -ForegroundColor Green
Write-Host "🚀 Starting Full XES3G5M Baseline Pipeline" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green

# Run the python full baseline runner
python src/full_baseline_runner.py --config configs/xes3g5m.yaml $args

Write-Host "=========================================================" -ForegroundColor Green
Write-Host "✅ Finished Full XES3G5M Baseline Pipeline" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
