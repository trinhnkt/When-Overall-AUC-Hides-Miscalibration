# run_full_assist2012_baselines.ps1
# Run full ASSISTments 2012 baseline experiments for seeds 2024 and 2025 (learner_based split).
# Usage: .\scripts\run_full_assist2012_baselines.ps1 [--fallback-akt] [--overwrite]

$env:PYTHONPATH="."

Write-Host "=========================================================" -ForegroundColor Green
Write-Host "🚀 Starting Full ASSISTments 2012 Baseline Pipeline" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green

# Run the python full baseline runner
python src/full_baseline_runner.py --config configs/assist2012.yaml $args

Write-Host "=========================================================" -ForegroundColor Green
Write-Host "✅ Finished Full ASSISTments 2012 Baseline Pipeline" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
