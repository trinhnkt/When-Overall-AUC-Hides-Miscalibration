import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, log_loss, mean_squared_error
from pathlib import Path
import argparse
import glob
import os

def compute_metrics(y_true, p_pred):
    """Computes standard KT metrics, dropping NaNs."""
    # Drop NaNs
    mask = ~np.isnan(p_pred)
    y_true = y_true[mask]
    p_pred = p_pred[mask]
    
    if len(y_true) == 0:
        return {
            "auc": np.nan, "acc": np.nan, "nll": np.nan, "rmse": np.nan, "n_nan": np.sum(~mask), "note": "no_predictions"
        }
    
    unique_classes = np.unique(y_true)
    auc = np.nan
    note = ""
    if len(unique_classes) < 2:
        note = f"only_one_class_{unique_classes[0]}"
    else:
        try:
            auc = roc_auc_score(y_true, p_pred)
        except Exception as e:
            note = str(e)
    
    # NLL/BCE
    try:
        nll = log_loss(y_true, p_pred, labels=[0, 1])
    except:
        nll = np.nan
        
    return {
        "auc": auc,
        "acc": accuracy_score(y_true, (p_pred >= 0.5).astype(int)),
        "nll": nll,
        "rmse": np.sqrt(mean_squared_error(y_true, p_pred)),
        "n_nan": np.sum(~mask),
        "note": note
    }

def main():
    parser = argparse.ArgumentParser(description="Compute metrics from predictions.")
    parser.add_argument("--prediction_dir", type=str, default="results/predictions")
    parser.add_argument("--strata_path", type=str, default="results/tables/kc_strata.csv")
    args = parser.parse_args()
    
    pred_dir = Path(args.prediction_dir)
    strata_path = Path(args.strata_path)
    
    if not pred_dir.exists():
        print(f"Prediction directory {pred_dir} not found.")
        return
        
    pred_files = glob.glob(str(pred_dir / "*.csv"))
    if not pred_files:
        print("No prediction files found.")
        return
        
    # Load strata if available
    strata_df = None
    if strata_path.exists():
        strata_df = pd.read_csv(strata_path)
        print(f"Loaded strata from {strata_path}")
        
    results = []
    bucket_results = []
    
    print(f"Processing {len(pred_files)} prediction files...")
    
    for f in pred_files:
        df = pd.read_csv(f)
        if df.empty: continue
        
        # Identifiers from filename or content
        # assist2012_learner_based_bkt_seed42.csv
        parts = Path(f).stem.split('_')
        # This is a bit fragile, better to use unique combinations in DF
        
        # Group by experiment
        groups = df.groupby(['dataset', 'split_mode', 'model', 'seed'])
        
        for name, group in groups:
            dataset, mode, model, seed = name
            
            # 1. Overall Metrics
            m = compute_metrics(group['y_true'].values, group['p_pred'].values)
            results.append({
                "dataset": dataset, "split_mode": mode, "model": model, "seed": seed, **m
            })
            
            # 2. Per-Bucket Metrics
            if strata_df is not None:
                # Join with strata
                # Filter strata for this experiment
                exp_strata = strata_df[(strata_df['dataset'] == dataset) & 
                                       (strata_df['split'] == mode) & 
                                       (strata_df['fold'] == (group['seed'].map({42:0, 123:1, 2026:2}).iloc[0] if mode == 'learner_based' else 0))]
                
                if not exp_strata.empty:
                    # Map kc_id to bucket
                    kc_to_bucket = exp_strata.set_index('kc_id')['bucket'].to_dict()
                    group = group.copy()
                    group['bucket'] = group['kc_id'].map(kc_to_bucket)
                    
                    for bucket, b_group in group.groupby('bucket'):
                        bm = compute_metrics(b_group['y_true'].values, b_group['p_pred'].values)
                        bucket_results.append({
                            "dataset": dataset,
                            "split_mode": mode,
                            "model": model,
                            "seed": seed,
                            "bucket": bucket,
                            "n_events": len(b_group),
                            "n_kcs": b_group['kc_id'].nunique(),
                            **bm
                        })

    # Save overall results
    df_overall = pd.DataFrame(results)
    if not df_overall.empty:
        df_overall.to_csv("results/tables/overall_results.csv", index=False)
        # Summary
        summary = df_overall.groupby(['dataset', 'split_mode', 'model']).agg({
            'auc': ['mean', 'std'], 'acc': ['mean', 'std'], 'nll': ['mean', 'std'], 'rmse': ['mean', 'std']
        })
        summary.columns = [f"{c[0]}_{c[1]}" for c in summary.columns]
        summary.reset_index().to_csv("results/tables/overall_results_summary.csv", index=False)

    # Save bucket results
    df_bucket = pd.DataFrame(bucket_results)
    if not df_bucket.empty:
        df_bucket.to_csv("results/tables/metric_per_bucket.csv", index=False)
        # Summary
        b_summary = df_bucket.groupby(['dataset', 'split_mode', 'model', 'bucket']).agg({
            'auc': ['mean', 'std'], 'acc': ['mean', 'std'], 'nll': ['mean', 'std'], 'rmse': ['mean', 'std'],
            'n_events': 'sum', 'n_kcs': 'first'
        })
        b_summary.columns = [f"{c[0]}_{c[1]}" if isinstance(c, tuple) and c[1] != '' else c[0] for c in b_summary.columns]
        b_summary.reset_index().to_csv("results/tables/metric_per_bucket_summary.csv", index=False)
        print(f"Saved bucket metrics to results/tables/metric_per_bucket.csv")

if __name__ == "__main__":
    main()
