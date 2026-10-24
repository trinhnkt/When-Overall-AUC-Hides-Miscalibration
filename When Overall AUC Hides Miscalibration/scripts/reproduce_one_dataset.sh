#!/usr/bin/env bash
# reproduce_one_dataset.sh
# Usage: ./scripts/reproduce_one_dataset.sh configs/assist2012.yaml

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <config_yaml_path>"
    exit 1
fi

CONFIG_PATH="$1"
export PYTHONPATH="."

echo "========================================="
echo "Starting Reproduction Pipeline for $CONFIG_PATH"
echo "========================================="

# 1. Preprocess raw data
echo "Running Preprocessing..."
python src/preprocess.py --config "$CONFIG_PATH"

# 2. Build splits
echo "Building splits..."
python src/three_split_constructor.py --config "$CONFIG_PATH"

# 3. Train baselines and generate predictions
echo "Running Baseline experiments..."
python src/baseline_runner.py --config "$CONFIG_PATH"

# 4. Stratify knowledge concepts (KC Strata)
echo "Computing KC Strata..."
DATASET_NAME=$(python -c "import yaml; print(yaml.safe_load(open('$CONFIG_PATH'))['dataset_name'])")
python src/kc_strata.py --dataset "$DATASET_NAME" --config "$CONFIG_PATH"

# 5. Evaluate bucket performance metrics
echo "Evaluating performance metrics per bucket..."
python src/metrics.py

# 6. Evaluate calibration (ECE)
echo "Evaluating calibration ECE..."
python src/calibration_eval.py

# 7. Evaluate Brier decomposition
echo "Evaluating Brier score decomposition..."
python src/brier_decomposition.py

# 8. Evaluate cold-start concepts
echo "Evaluating cold-start concept groups..."
python src/cold_start_split.py

# 9. Run sensitivity analysis
echo "Running bucket threshold sensitivity analysis..."
python src/sensitivity_analysis.py

# 10. Run leakage checkpoints audit
echo "Running leakage audit checkpoints..."
python src/leakage_checklist_runner.py

# 11. Plot reliability diagrams
echo "Generating reliability diagrams..."
python src/reliability_diagram_plotter.py

# 12. Generate report and paper tables
echo "Generating publication artifacts and reports..."
python src/report_generator.py --project-root . --output results/reports/p0_diagnostic_report.md

echo "========================================="
echo "Pipeline execution for $CONFIG_PATH complete."
echo "========================================="
