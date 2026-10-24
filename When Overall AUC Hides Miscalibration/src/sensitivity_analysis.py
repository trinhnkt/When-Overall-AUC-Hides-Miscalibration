import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import glob
import yaml
from src.metrics import compute_metrics
from src.calibration_eval import compute_ece

def get_bucket(freq, thresholds):
    if freq == 0:
        return "strict_cold_start"
    elif freq < thresholds[0]:
        return "very_sparse"
    elif freq < thresholds[1]:
        return "sparse"
    elif freq < thresholds[2]:
        return "medium"
    else:
        return "dense"

def main():
    parser = argparse.ArgumentParser(description="Threshold sensitivity analysis.")
    parser.add_argument("--prediction_dir", type=str, default="results/predictions")
    parser.add_argument("--strata_path", type=str, default="results/tables/kc_strata.csv")
    args = parser.parse_args()
    
    pred_dir = Path(args.prediction_dir)
    strata_path = Path(args.strata_path)
    
    if not pred_dir.exists() or not strata_path.exists():
        print("Required files not found.")
        return
        
    strata_df = pd.read_csv(strata_path)
    pred_files = glob.glob(str(pred_dir / "*.csv"))
    
    settings = {
        "Main": [20, 100, 500],
        "Alt_1": [10, 50, 250],
        "Alt_2": [30, 150, 750]
    }
    
    results = []
    
    print(f"Running sensitivity analysis for {len(pred_files)} prediction files...")
    
    for f in pred_files:
        df = pd.read_csv(f)
        if df.empty: continue
        
        groups = df.groupby(['dataset', 'split_mode', 'model', 'seed'])
        for name, group in groups:
            dataset, mode, model, seed = name
            
            # Filter strata
            exp_strata = strata_df[(strata_df['dataset'] == dataset) & 
                                   (strata_df['split'] == mode) & 
                                   (strata_df['fold'] == (group['seed'].map({42:0, 123:1, 2026:2}).iloc[0] if mode == 'learner_based' else 0))]
            
            if exp_strata.empty: continue
            
            # Current thresholds
            for s_name, thresholds in settings.items():
                kc_to_bucket = {row['kc_id']: get_bucket(row['train_freq'], thresholds) for _, row in exp_strata.iterrows()}
                
                temp_group = group.copy()
                temp_group['bucket'] = temp_group['kc_id'].map(kc_to_bucket)
                
                for bucket, b_group in temp_group.groupby('bucket'):
                    m = compute_metrics(b_group['y_true'].values, b_group['p_pred'].values)
                    ece, _, _, _, _ = compute_ece(b_group['y_true'].values, b_group['p_pred'].values)
                    
                    results.append({
                        "dataset": dataset, "split_mode": mode, "model": model, "seed": seed,
                        "setting": s_name, "bucket": bucket,
                        "auc": m['auc'], "ece": ece, "brier": m['rmse']**2, # RMSE^2 is Brier
                        "n_events": len(b_group)
                    })
            
            # Alt 3: Quantile-based
            # q25, q50, q75 of train_freq
            q = exp_strata['train_freq'].quantile([0.25, 0.5, 0.75]).values
            # Ensure they are unique
            q = sorted(list(set(q)))
            if len(q) < 3:
                # Fallback if quantiles are not unique (e.g. lots of zeros)
                q = [q[0], q[0]+1, q[0]+2] if len(q) > 0 else [1, 2, 3]
                while len(q) < 3: q.append(q[-1]+1)
            
            kc_to_bucket_q = {row['kc_id']: get_bucket(row['train_freq'], q[:3]) for _, row in exp_strata.iterrows()}
            temp_group_q = group.copy()
            temp_group_q['bucket'] = temp_group_q['kc_id'].map(kc_to_bucket_q)
            
            for bucket, b_group in temp_group_q.groupby('bucket'):
                m = compute_metrics(b_group['y_true'].values, b_group['p_pred'].values)
                ece, _, _, _, _ = compute_ece(b_group['y_true'].values, b_group['p_pred'].values)
                results.append({
                    "dataset": dataset, "split_mode": mode, "model": model, "seed": seed,
                    "setting": "Alt_Quantile", "bucket": bucket,
                    "auc": m['auc'], "ece": ece, "brier": m['rmse']**2,
                    "n_events": len(b_group)
                })

    pd.DataFrame(results).to_csv("results/tables/sensitivity_analysis.csv", index=False)
    print("Sensitivity analysis complete. Saved to results/tables/sensitivity_analysis.csv")

if __name__ == "__main__":
    main()
