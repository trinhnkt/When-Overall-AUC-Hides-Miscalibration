# run_full_junyi_baselines.ps1
# Run full Junyi Academy baseline experiments for seeds 2024 and 2025 (learner_based split).
# Usage: .\scripts\run_full_junyi_baselines.ps1 [--fallback-akt] [--overwrite]

$env:PYTHONPATH="."

Write-Host "=========================================================" -ForegroundColor Green
Write-Host "🚀 Starting Full Junyi Academy Baseline Pipeline" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green

# Run the python full baseline runner
python src/full_baseline_runner.py --config configs/junyi.yaml $args

Write-Host "=========================================================" -ForegroundColor Green
Write-Host "✅ Finished Full Junyi Academy Baseline Pipeline" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
