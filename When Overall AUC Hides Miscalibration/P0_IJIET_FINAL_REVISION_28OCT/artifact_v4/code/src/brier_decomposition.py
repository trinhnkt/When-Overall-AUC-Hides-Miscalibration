import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import glob
import os

def compute_brier_score(y_true, p_pred):
    """Computes basic Brier score."""
    mask = ~np.isnan(p_pred)
    y_true = y_true[mask]
    p_pred = p_pred[mask]
    if len(y_true) == 0: return np.nan
    return np.mean((p_pred - y_true)**2)

def compute_brier_decomposition(y_true, p_pred, n_bins=15):
    """
    Computes Brier score decomposition: BS = UNC - RES + REL.
    """
    mask = ~np.isnan(p_pred)
    y_true = y_true[mask]
    p_pred = p_pred[mask]
    
    if len(y_true) == 0:
        return np.nan, np.nan, np.nan, np.nan
    
    N = len(y_true)
    y_bar = np.mean(y_true)
    
    # 1. Uncertainty (UNC)
    unc = y_bar * (1 - y_bar)
    
    # Binning for REL and RES
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    rel = 0
    res = 0
    
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (p_pred > bin_lower) & (p_pred <= bin_upper)
        if bin_lower == 0:
            in_bin |= (p_pred == 0)
            
        n_m = np.sum(in_bin)
        if n_m > 0:
            acc_m = np.mean(y_true[in_bin])
            conf_m = np.mean(p_pred[in_bin])
            
            rel += n_m * (conf_m - acc_m)**2
            res += n_m * (acc_m - y_bar)**2
            
    rel /= N
    res /= N
    
    brier = compute_brier_score(y_true, p_pred)
    
    return brier, unc, rel, res

def main():
    parser = argparse.ArgumentParser(description="Compute Brier decomposition.")
    parser.add_argument("--prediction_dir", type=str, default="results/predictions")
    parser.add_argument("--strata_path", type=str, default="results/tables/kc_strata.csv")
    parser.add_argument("--n_bins", type=int, default=15)
    args = parser.parse_args()
    
    pred_dir = Path(args.prediction_dir)
    strata_path = Path(args.strata_path)
    
    if not pred_dir.exists(): return
    
    pred_files = glob.glob(str(pred_dir / "*.csv"))
    if not pred_files: return
    
    strata_df = None
    if strata_path.exists():
        strata_df = pd.read_csv(strata_path)
        
    results = []
    
    print(f"Processing {len(pred_files)} prediction files for Brier decomposition...")
    
    for f in pred_files:
        df = pd.read_csv(f)
        if df.empty: continue
        
        groups = df.groupby(['dataset', 'split_mode', 'model', 'seed'])
        for name, group in groups:
            dataset, mode, model, seed = name
            
            if strata_df is not None:
                exp_strata = strata_df[(strata_df['dataset'] == dataset) & 
                                       (strata_df['split'] == mode) & 
                                       (strata_df['fold'] == (group['seed'].map({42:0, 123:1, 2026:2}).iloc[0] if mode == 'learner_based' else 0))]
                
                if not exp_strata.empty:
                    kc_to_bucket = exp_strata.set_index('kc_id')['bucket'].to_dict()
                    group = group.copy()
                    group['bucket'] = group['kc_id'].map(kc_to_bucket)
                    
                    for bucket, b_group in group.groupby('bucket'):
                        bs, unc, rel, res = compute_brier_decomposition(b_group['y_true'].values, b_group['p_pred'].values, n_bins=args.n_bins)
                        results.append({
                            "dataset": dataset, "split_mode": mode, "model": model, "seed": seed, "bucket": bucket,
                            "brier": bs, "uncertainty": unc, "reliability": rel, "resolution": res, "n_events": len(b_group)
                        })
            else:
                bs, unc, rel, res = compute_brier_decomposition(group['y_true'].values, group['p_pred'].values, n_bins=args.n_bins)
                results.append({
                    "dataset": dataset, "split_mode": mode, "model": model, "seed": seed, "bucket": "overall",
                    "brier": bs, "uncertainty": unc, "reliability": rel, "resolution": res, "n_events": len(group)
                })
                
    df_results = pd.DataFrame(results)
    out_dir = Path("results/tables")
    out_dir.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(out_dir / "brier_decomposition.csv", index=False)
    
    # Summary
    if not df_results.empty:
        summary = df_results.groupby(['dataset', 'split_mode', 'model', 'bucket']).agg({
            'brier': ['mean', 'std'], 'uncertainty': 'mean', 'reliability': 'mean', 'resolution': 'mean'
        })
        summary.columns = [f"{c[0]}_{c[1]}" if isinstance(c, tuple) and c[1] != '' else c[0] for c in summary.columns]
        summary = summary.reset_index()
        summary.to_csv(out_dir / "brier_decomposition_summary.csv", index=False)
        
    print(f"Saved Brier decomposition to {out_dir}")

if __name__ == "__main__":
    main()
