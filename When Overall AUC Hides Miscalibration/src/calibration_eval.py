import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import glob
import os

def compute_ece(y_true, p_pred, n_bins=15):
    """
    Computes Expected Calibration Error (ECE) using fixed-width bins.
    Returns ece and bin-level details.
    """
    # Drop NaNs
    mask = ~np.isnan(p_pred)
    y_true = y_true[mask]
    p_pred = p_pred[mask]
    
    if len(y_true) == 0:
        return np.nan, [0] * n_bins, [np.nan] * n_bins, [np.nan] * n_bins, [np.nan] * n_bins
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    ece = 0
    bin_counts = []
    bin_confs = []
    bin_accs = []
    bin_gaps = []
    
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        # Calculated |confidence - accuracy| in each bin
        in_bin = (p_pred > bin_lower) & (p_pred <= bin_upper)
        # Edge case for bin 0
        if bin_lower == 0:
            in_bin |= (p_pred == 0)
            
        prop_in_bin = np.mean(in_bin)
        
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(p_pred[in_bin])
            gap = np.abs(avg_confidence_in_bin - accuracy_in_bin)
            ece += gap * prop_in_bin
            
            bin_counts.append(np.sum(in_bin))
            bin_confs.append(avg_confidence_in_bin)
            bin_accs.append(accuracy_in_bin)
            bin_gaps.append(gap)
        else:
            bin_counts.append(0)
            bin_confs.append(np.nan)
            bin_accs.append(np.nan)
            bin_gaps.append(np.nan)
            
    return ece, bin_counts, bin_confs, bin_accs, bin_gaps

def main():
    parser = argparse.ArgumentParser(description="Compute ECE from predictions.")
    parser.add_argument("--prediction_dir", type=str, default="results/predictions")
    parser.add_argument("--strata_path", type=str, default="results/tables/kc_strata.csv")
    parser.add_argument("--n_bins", type=int, default=15)
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
        
    strata_df = None
    if strata_path.exists():
        strata_df = pd.read_csv(strata_path)
        
    ece_results = []
    bin_details = []
    
    print(f"Processing {len(pred_files)} prediction files for ECE...")
    
    for f in pred_files:
        df = pd.read_csv(f)
        if df.empty: continue
        
        groups = df.groupby(['dataset', 'split_mode', 'model', 'seed'])
        for name, group in groups:
            dataset, mode, model, seed = name
            
            # Map buckets if strata available
            if strata_df is not None:
                exp_strata = strata_df[(strata_df['dataset'] == dataset) & 
                                       (strata_df['split'] == mode) & 
                                       (strata_df['fold'] == (group['seed'].map({42:0, 123:1, 2026:2}).iloc[0] if mode == 'learner_based' else 0))]
                
                if not exp_strata.empty:
                    kc_to_bucket = exp_strata.set_index('kc_id')['bucket'].to_dict()
                    group = group.copy()
                    group['bucket'] = group['kc_id'].map(kc_to_bucket)
                    
                    for bucket, b_group in group.groupby('bucket'):
                        ece, counts, confs, accs, gaps = compute_ece(b_group['y_true'].values, b_group['p_pred'].values, n_bins=args.n_bins)
                        
                        ece_results.append({
                            "dataset": dataset, "split_mode": mode, "model": model, "seed": seed, "bucket": bucket,
                            "ece": ece, "n_events": len(b_group), "n_bins": args.n_bins
                        })
                        
                        for i in range(args.n_bins):
                            bin_details.append({
                                "dataset": dataset, "split_mode": mode, "model": model, "seed": seed, "bucket": bucket,
                                "bin_id": i, "n_bin": counts[i], "conf_bin": confs[i], "acc_bin": accs[i], "gap_bin": gaps[i]
                            })
            else:
                # Overall only if no strata
                ece, counts, confs, accs, gaps = compute_ece(group['y_true'].values, group['p_pred'].values, n_bins=args.n_bins)
                ece_results.append({
                    "dataset": dataset, "split_mode": mode, "model": model, "seed": seed, "bucket": "overall",
                    "ece": ece, "n_events": len(group), "n_bins": args.n_bins
                })
                
    # Save results
    df_ece = pd.DataFrame(ece_results)
    df_bins = pd.DataFrame(bin_details)
    
    out_dir = Path("results/tables")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    df_ece.to_csv(out_dir / "ece_per_bucket.csv", index=False)
    df_bins.to_csv(out_dir / "ece_per_bucket_bins.csv", index=False)
    print(f"Saved ECE results to {out_dir}")

if __name__ == "__main__":
    main()
