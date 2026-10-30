#!/usr/bin/env bash
# run_full_xes3g5m_baselines.sh
# Run full XES3G5M baseline experiments for seeds 2024 and 2025 (learner_based split).
# Usage: bash scripts/run_full_xes3g5m_baselines.sh [--fallback-akt] [--overwrite]

set -e

export PYTHONPATH="."

echo "========================================================="
echo "🚀 Starting Full XES3G5M Baseline Pipeline"
echo "========================================================="

# Run the python full baseline runner
python src/full_baseline_runner.py --config configs/xes3g5m.yaml "$@"

echo "========================================================="
echo "✅ Finished Full XES3G5M Baseline Pipeline"
echo "========================================================="
