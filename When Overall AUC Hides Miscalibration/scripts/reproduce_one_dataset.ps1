param (
    [string]$ConfigPath
)

if (-not $ConfigPath) {
    Write-Error "Usage: ./scripts/reproduce_one_dataset.ps1 <config_yaml_path>"
    exit 1
}

# Normalize backslashes to forward slashes to prevent escape sequences in Python
$ConfigPath = $ConfigPath.Replace('\', '/')

$env:PYTHONPATH="."

Write-Host "========================================="
Write-Host "Starting PowerShell Reproduction Pipeline for $ConfigPath"
Write-Host "========================================="

# 1. Preprocess raw data
Write-Host "Running Preprocessing..."
python src/preprocess.py --config "$ConfigPath"

# 2. Build splits
Write-Host "Building splits..."
python src/three_split_constructor.py --config "$ConfigPath"

# 3. Train baselines and generate predictions
Write-Host "Running Baseline experiments..."
python src/baseline_runner.py --config "$ConfigPath"

# 4. Stratify knowledge concepts (KC Strata)
Write-Host "Computing KC Strata..."
$dataset_name = python -c "import yaml; print(yaml.safe_load(open('$ConfigPath'))['dataset_name'])"
python src/kc_strata.py --dataset "$dataset_name" --config "$ConfigPath"

# 5. Evaluate bucket performance metrics
Write-Host "Evaluating performance metrics per bucket..."
python src/metrics.py

# 6. Evaluate calibration (ECE)
Write-Host "Evaluating calibration ECE..."
python src/calibration_eval.py

# 7. Evaluate Brier decomposition
Write-Host "Evaluating Brier score decomposition..."
python src/brier_decomposition.py

# 8. Evaluate cold-start concepts
Write-Host "Evaluating cold-start concept groups..."
python src/cold_start_split.py

# 9. Run sensitivity analysis
Write-Host "Running bucket threshold sensitivity analysis..."
python src/sensitivity_analysis.py

# 10. Run leakage checkpoints audit
Write-Host "Running leakage audit checkpoints..."
python src/leakage_checklist_runner.py

# 11. Plot reliability diagrams
Write-Host "Generating reliability diagrams..."
python src/reliability_diagram_plotter.py

# 12. Generate report and paper tables
Write-Host "Generating publication artifacts and reports..."
python src/report_generator.py --project-root . --output results/reports/p0_diagnostic_report.md

Write-Host "========================================="
Write-Host "PowerShell Pipeline execution for $ConfigPath complete."
Write-Host "========================================="
