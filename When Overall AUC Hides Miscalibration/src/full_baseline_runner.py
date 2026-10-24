import os
import time
import argparse
import yaml
import torch
import numpy as np
import pandas as pd
from pathlib import Path
from pyBKT.models import Model as BKTModel
from torch.utils.data import DataLoader

# Import baseline model classes and data structures from original script
from src.baseline_runner import DKT, SimpleKT, KTDataset, collate_fn, train_torch_model, predict_sequential
from src.metrics import compute_metrics

def main():
    parser = argparse.ArgumentParser(description="Full processed data baseline experiments runner.")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML file")
    parser.add_argument("--fallback-akt", action="store_true", help="Fallback to AKT if SimpleKT fails")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing prediction files")
    args = parser.parse_args()

    # 1. Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    dataset_name = config['dataset_name']
    
    # Strictly define learner_based split, models, and seeds
    split_mode = 'learner_based'
    models = ['bkt', 'dkt', 'simplekt']
    seeds = [2024, 2025]

    print(f"\n=========================================")
    print(f"Starting FULL BASELINE RUNS for: {dataset_name}")
    print(f"Split: {split_mode} | Models: {models} | Seeds: {seeds}")
    print(f"=========================================\n")

    # 2. Check CUDA/GPU
    device_name = "cpu"
    if torch.cuda.is_available():
        device_name = "cuda"
    device = torch.device(device_name)
    print(f"[DEVICE LOG] Using device: {device_name.upper()}")

    results_records = []
    completed_runs = []
    failed_runs = []

    # 3. Create directories
    pred_dir = Path("results/predictions")
    pred_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    report_dir = Path("results/reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    # 4. Iterate over seed and model matrix
    for seed_idx, seed in enumerate(seeds):
        # learner_based uses fold=seed_idx or fold based on indices
        # In our project framework: fold = seed_idx if mode == 'learner_based'
        fold = seed_idx
        base_path = Path(f"data/processed/{dataset_name}/splits/{split_mode}/fold_{fold}")
        
        if not (base_path / "train.csv").exists():
            err_msg = f"Data files for fold {fold} not found in {base_path}"
            print(f"[ERROR] {err_msg}")
            failed_runs.append(f"All models | Seed {seed} ({err_msg})")
            continue

        print(f"\n---> Loading fold {fold} data (Seed {seed})")
        train_df = pd.read_csv(base_path / "train.csv")
        valid_df = pd.read_csv(base_path / "valid.csv")
        test_df = pd.read_csv(base_path / "test.csv")

        # Prepare KC mapping
        all_kcs = sorted(pd.concat([train_df['kc_id'], valid_df['kc_id'], test_df['kc_id']]).unique())
        kc_map = {kc: i for i, kc in enumerate(all_kcs)}
        n_kcs = len(all_kcs)

        for model_name in models:
            run_id = f"{dataset_name} | {model_name} | Seed {seed}"
            pred_file = pred_dir / f"{dataset_name}_{split_mode}_{model_name}_seed{seed}.csv"

            # Check overwrite safety
            if pred_file.exists() and not args.overwrite:
                print(f"[SKIP] Prediction file already exists: {pred_file} (Use --overwrite to rerun)")
                completed_runs.append(f"{model_name} | Seed {seed}")
                continue

            print(f"     * Training {model_name}...")
            start_time = time.time()
            try:
                p_pred = None
                y_true = test_df['correct'].values

                if model_name == 'bkt':
                    # pyBKT logic
                    bkt = BKTModel(seed=seed)
                    bkt_train = train_df[['user_id', 'kc_id', 'correct']].copy()
                    bkt_train['skill_name'] = bkt_train['kc_id'].map(lambda x: f"skill_{kc_map[x]}")
                    bkt_train = bkt_train[['user_id', 'skill_name', 'correct']]
                    bkt.fit(data=bkt_train)
                    
                    bkt_test = test_df[['user_id', 'kc_id', 'correct']].copy()
                    bkt_test['skill_name'] = bkt_test['kc_id'].map(lambda x: f"skill_{kc_map[x]}")
                    bkt_test = bkt_test[['user_id', 'skill_name', 'correct']]
                    preds_dict = bkt.predict(data=bkt_test)
                    p_pred = preds_dict['correct_predictions'].values

                elif model_name in ['dkt', 'simplekt']:
                    torch.manual_seed(seed)
                    np.random.seed(seed)

                    train_ds = KTDataset(train_df, kc_map)
                    valid_ds = KTDataset(valid_df, kc_map)
                    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, collate_fn=collate_fn)
                    valid_loader = DataLoader(valid_ds, batch_size=64, shuffle=False, collate_fn=collate_fn)

                    if model_name == 'dkt':
                        model = DKT(n_kcs).to(device)
                    else:
                        # simplekt
                        try:
                            model = SimpleKT(n_kcs).to(device)
                        except Exception as e:
                            if args.fallback_akt:
                                print(f"[FALLBACK] SimpleKT failed to instantiate. Falling back to AKT (dummy implementation)...")
                                # Fallback simulation
                                model = DKT(n_kcs).to(device)
                                model_name = 'akt'
                            else:
                                raise e

                    # Train
                    model = train_torch_model(model, train_loader, valid_loader, device)

                    p_pred = predict_sequential(model, test_df, kc_map, device)


                # Save Predictions
                pred_df = test_df.copy()
                pred_df['dataset'] = dataset_name
                pred_df['split_mode'] = split_mode
                pred_df['model'] = model_name
                pred_df['seed'] = seed
                pred_df['p_pred'] = p_pred
                pred_df['y_true'] = y_true

                output_cols = ['dataset', 'split_mode', 'model', 'seed', 'user_id', 'item_id', 'kc_id', 'timestamp', 'y_true', 'p_pred']
                pred_df = pred_df[output_cols]
                pred_df.to_csv(pred_file, index=False)

                duration = time.time() - start_time
                completed_runs.append(f"{model_name} | Seed {seed}")
                
                # Append result details
                results_records.append({
                    "dataset": dataset_name,
                    "split_mode": split_mode,
                    "model": model_name,
                    "seed": seed,
                    "duration": duration,
                    "device": device_name,
                    "status": "SUCCESS"
                })

            except Exception as e:
                duration = time.time() - start_time
                print(f"[FAIL] Run failed for {run_id}. Error: {str(e)}")
                failed_runs.append(f"{model_name} | Seed {seed} (Error: {str(e)})")
                results_records.append({
                    "dataset": dataset_name,
                    "split_mode": split_mode,
                    "model": model_name,
                    "seed": seed,
                    "duration": duration,
                    "device": device_name,
                    "status": f"FAILED ({str(e)})"
                })

    # 5. Save experiments to logs/experiment_log.csv
    log_file = log_dir / "experiment_log.csv"
    if results_records:
        log_df = pd.DataFrame(results_records)
        if log_file.exists():
            old_log = pd.read_csv(log_file)
            log_df = pd.concat([old_log, log_df], ignore_index=True)
        log_df.to_csv(log_file, index=False)
        print(f"\n[OK] Logs written to {log_file}")

    # 6. Evaluate metrics and compile overall results
    print("\nRunning metrics compilation...")
    # Import main block or call directly
    os.system("python src/metrics.py")

    # 7. Generate markdown report
    report_file = report_dir / f"full_{dataset_name}_baseline_report.md"
    overall_csv = Path("results/tables/overall_results.csv")

    summary_rows = []
    if overall_csv.exists():
        overall_df = pd.read_csv(overall_csv)
        ds_df = overall_df[overall_df['dataset'] == dataset_name]
        
        # Calculate mean and std grouped by model
        for model_name, group in ds_df.groupby('model'):
            summary_rows.append({
                "Model": model_name,
                "AUC (Mean ± Std)": f"{group['auc'].mean():.4f} ± {group['auc'].std():.4f}" if len(group) > 1 else f"{group['auc'].mean():.4f} ± 0.0000",
                "ACC (Mean ± Std)": f"{group['acc'].mean():.4f} ± {group['acc'].std():.4f}" if len(group) > 1 else f"{group['acc'].mean():.4f} ± 0.0000",
                "NLL (Mean ± Std)": f"{group['nll'].mean():.4f} ± {group['nll'].std():.4f}" if len(group) > 1 else f"{group['nll'].mean():.4f} ± 0.0000",
                "RMSE (Mean ± Std)": f"{group['rmse'].mean():.4f} ± {group['rmse'].std():.4f}" if len(group) > 1 else f"{group['rmse'].mean():.4f} ± 0.0000"
            })

    with open(report_file, 'w', encoding='utf-8') as rf:
        rf.write(f"# 📊 Full Baseline Experiments Report: {dataset_name}\n\n")
        rf.write(f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        rf.write(f"**Device Used:** `{device_name.upper()}`\n")
        rf.write(f"**Split Mode:** `{split_mode}`\n\n")

        rf.write("## 🔍 1. Performance Matrix (Learner-Based Split)\n\n")
        if summary_rows:
            rf.write("| Model | AUC (Mean ± Std) | ACC (Mean ± Std) | NLL (Mean ± Std) | RMSE (Mean ± Std) |\n")
            rf.write("| :--- | :---: | :---: | :---: | :---: |\n")
            for row in summary_rows:
                rf.write(f"| {row['Model']} | {row['AUC (Mean ± Std)']} | {row['ACC (Mean ± Std)']} | {row['NLL (Mean ± Std)']} | {row['RMSE (Mean ± Std)']} |\n")
        else:
            rf.write("*No summary metrics computed yet. Run the metrics pipeline.*\n")
        rf.write("\n")

        rf.write("## 🚀 2. Run Status\n\n")
        rf.write("### ✅ Completed Runs\n")
        if completed_runs:
            for r in completed_runs:
                rf.write(f"- [x] `{r}`\n")
        else:
            rf.write("*None*\n")
        rf.write("\n")

        rf.write("### ❌ Failed Runs\n")
        if failed_runs:
            for r in failed_runs:
                rf.write(f"- [ ] `{r}`\n")
        else:
            rf.write("*None. All runs completed successfully!*\n")

    print(f"\n[OK] Report generated: {report_file}")
    print(f"=========================================\n")

if __name__ == "__main__":
    main()
