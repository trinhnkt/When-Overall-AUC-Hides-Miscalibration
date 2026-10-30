#!/usr/bin/env bash
# run_full_assist2012_baselines.sh
# Run full ASSISTments 2012 baseline experiments for seeds 2024 and 2025 (learner_based split).
# Usage: bash scripts/run_full_assist2012_baselines.sh [--fallback-akt] [--overwrite]

set -e

export PYTHONPATH="."

echo "========================================================="
echo "🚀 Starting Full ASSISTments 2012 Baseline Pipeline"
echo "========================================================="

# Run the python full baseline runner
python src/full_baseline_runner.py --config configs/assist2012.yaml "$@"

echo "========================================================="
echo "✅ Finished Full ASSISTments 2012 Baseline Pipeline"
echo "========================================================="
