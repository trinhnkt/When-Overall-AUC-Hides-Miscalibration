#!/usr/bin/env bash
# run_all_full_baselines.sh
# Master script to run all full baseline experiments for P0 paper.
# Usage: bash scripts/run_all_full_baselines.sh [--fallback-akt] [--overwrite]

set -e

export PYTHONPATH="."

echo "========================================================================"
echo "🌟 Starting MASTER PIPELINE for Reproducible KT baseline experiments"
echo "========================================================================"

# Run assist2012
bash scripts/run_full_assist2012_baselines.sh "$@"

# Run junyi
bash scripts/run_full_junyi_baselines.sh "$@"

# Run xes3g5m
bash scripts/run_full_xes3g5m_baselines.sh "$@"

echo "========================================================================"
echo "🎉 MASTER PIPELINE completed successfully for all datasets!"
echo "========================================================================"
