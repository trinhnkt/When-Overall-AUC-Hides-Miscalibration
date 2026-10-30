#!/usr/bin/env bash
# run_full_junyi_baselines.sh
# Run full Junyi Academy baseline experiments for seeds 2024 and 2025 (learner_based split).
# Usage: bash scripts/run_full_junyi_baselines.sh [--fallback-akt] [--overwrite]

set -e

export PYTHONPATH="."

echo "========================================================="
echo "🚀 Starting Full Junyi Academy Baseline Pipeline"
echo "========================================================="

# Run the python full baseline runner
python src/full_baseline_runner.py --config configs/junyi.yaml "$@"

echo "========================================================="
echo "✅ Finished Full Junyi Academy Baseline Pipeline"
echo "========================================================="
