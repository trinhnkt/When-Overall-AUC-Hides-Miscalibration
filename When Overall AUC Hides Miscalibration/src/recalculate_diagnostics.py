#!/usr/bin/env python3
"""
src/recalculate_diagnostics.py

Recalculate all KT evaluation diagnostics from raw prediction files
to ensure absolute logic consistency and data integrity.
"""

import os
import glob
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import roc_auc_score, mean_squared_error

def compute_ece(y_true, p_pred, n_bins=15):
    N = len(y_true)
    if N == 0:
        return np.nan
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    ece = 0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (p_pred > bin_lower) & (p_pred <= bin_upper)
        if bin_lower == 0:
            in_bin |= (p_pred == 0)
        
        n_m = np.sum(in_bin)
        if n_m > 0:
            acc_m = np.mean(y_true[in_bin])
            conf_m = np.mean(p_pred[in_bin])
            ece += (n_m / N) * np.abs(conf_m - acc_m)
            
    return ece

def compute_brier_decomposition(y_true, p_pred, n_bins=15):
    N = len(y_true)
    if N == 0:
        return np.nan, np.nan, np.nan, np.nan
    
    y_bar = np.mean(y_true)
    unc = y_bar * (1.0 - y_bar)
    
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
    brier = np.mean((p_pred - y_true)**2)
    return brier, unc, rel, res

def calculate_metrics(y_true, p_pred):
    if len(y_true) == 0:
        return np.nan, np.nan, np.nan, np.nan
    
    # Clip predictions to prevent extreme NLL anomalies
    p_clipped = np.clip(p_pred, 1e-15, 1.0 - 1e-15)
    
    # AUC
    if len(np.unique(y_true)) >= 2:
        auc = roc_auc_score(y_true, p_clipped)
    else:
        auc = np.nan
        
    # ACC
    acc = np.mean(y_true == (p_clipped >= 0.5))
    
    # NLL
    nll = -np.mean(y_true * np.log(p_clipped) + (1.0 - y_true) * np.log(1.0 - p_clipped))
    
    # RMSE
    rmse = np.sqrt(np.mean((p_clipped - y_true)**2))
    
    return auc, acc, nll, rmse

def main():
    print("Initializing Recalculation of KT Diagnostics...")
    
    # 1. Load KC strata mapping
    strata_path = Path("results/tables/kc_strata.csv")
    if not strata_path.exists():
        raise FileNotFoundError(f"strata file not found at {strata_path}")
    
    strata_df = pd.read_csv(strata_path)
    # Filter only official datasets
    strata_df = strata_df[strata_df['dataset'].isin(['assist2012', 'junyi', 'xes3g5m'])]
    
    # Map (dataset, split, kc_id) to bucket and train_freq
    strata_map = {}
    for _, row in strata_df.iterrows():
        key = (row['dataset'], row['split'], str(row['kc_id']).replace('.0', ''))
        strata_map[key] = {
            'bucket': row['bucket'],
            'train_freq': row['train_freq']
        }
    
    # 2. Scan and load prediction files
    pred_dir = Path("results/predictions")
    pred_files = glob.glob(str(pred_dir / "*.csv"))
    
    overall_rows = []
    bucket_rows = []
    cold_start_rows = []
    
    print(f"Scanned {len(pred_files)} prediction files.")
    
    for f_path in pred_files:
        path = Path(f_path)
        name = path.name
        parts = name.replace(".csv", "").split("_")
        
        # Exclude debug/test/gputest runs
        if "test" in name.lower() or "gpu" in name.lower():
            continue
            
        # Verify if it is an official run
        dataset = parts[0]
        if dataset not in ['assist2012', 'junyi', 'xes3g5m']:
            continue
            
        # Parse split mode, model and seed from name
        # Examples:
        # assist2012_learner_based_bkt_seed42.csv
        # assist2012_temporal_bkt_seed42.csv
        model = None
        seed = None
        if "learner_based" in name:
            split_mode = "learner_based"
            for idx, p in enumerate(parts):
                if p in ['bkt', 'dkt', 'simplekt']:
                    model = p
                    seed_part = parts[idx + 1]
                    seed = int(seed_part.replace("seed", ""))
                    break
        elif "temporal" in name:
            split_mode = "temporal"
            for idx, p in enumerate(parts):
                if p in ['bkt', 'dkt', 'simplekt']:
                    model = p
                    seed_part = parts[idx + 1]
                    seed = int(seed_part.replace("seed", ""))
                    break
        else:
            continue
            
        if model is None or seed is None:
            continue
            
        print(f"Processing: {dataset} | {split_mode} | {model} | seed {seed} ...")
        
        df = pd.read_csv(path)
        if df.empty:
            continue
            
        # Drop interactions with kc_id == -1 or missing predictions
        df = df.dropna(subset=['y_true', 'p_pred'])
        df = df[df['kc_id'].astype(str) != "-1"]
        df = df[df['kc_id'].astype(str) != "nan"]
        
        if len(df) == 0:
            print(f"Warning: file {name} has no valid evaluation events after filtering.")
            continue
            
        y_true = df['y_true'].values.astype(int)
        p_pred = df['p_pred'].values.astype(float)
        kc_ids = df['kc_id'].astype(str).str.replace(r'\.0$', '', regex=True).values
        
        # A. Calculate Overall Metrics
        auc, acc, nll, rmse = calculate_metrics(y_true, p_pred)
        overall_rows.append({
            'dataset': dataset,
            'split_mode': split_mode,
            'model': model,
            'seed': seed,
            'auc': auc,
            'acc': acc,
            'nll': nll,
            'rmse': rmse
        })
        
        # Map each event to bucket and train_freq
        buckets = []
        train_freqs = []
        for kc in kc_ids:
            key = (dataset, split_mode, kc)
            if key in strata_map:
                buckets.append(strata_map[key]['bucket'])
                train_freqs.append(strata_map[key]['train_freq'])
            else:
                # If KC is not in strata train fold, frequency is 0 (cold start!)
                buckets.append('strict_cold_start')
                train_freqs.append(0)
                
        df['bucket'] = buckets
        df['train_freq'] = train_freqs
        
        # B. Calculate Metrics by Bucket
        for bucket, b_df in df.groupby('bucket'):
            b_y_true = b_df['y_true'].values.astype(int)
            b_p_pred = b_df['p_pred'].values.astype(float)
            
            b_auc, b_acc, b_nll, b_rmse = calculate_metrics(b_y_true, b_p_pred)
            b_ece = compute_ece(b_y_true, b_p_pred)
            brier, unc, rel, res = compute_brier_decomposition(b_y_true, b_p_pred)
            
            bucket_rows.append({
                'dataset': dataset,
                'split_mode': split_mode,
                'model': model,
                'seed': seed,
                'bucket': bucket,
                'n_kcs': len(b_df['kc_id'].unique()),
                'n_events': len(b_df),
                'auc': b_auc,
                'acc': b_acc,
                'nll': b_nll,
                'rmse': b_rmse,
                'ece': b_ece,
                'brier': brier,
                'uncertainty': unc,
                'reliability': rel,
                'resolution': res
            })
            
        # C. Calculate Cold-Start Metrics
        # Groups: strict (train_freq == 0), k5 (train_freq <= 5), k10 (train_freq <= 10), warm (train_freq > 10)
        cold_start_groups = {
            'strict': df[df['train_freq'] == 0],
            'k5': df[df['train_freq'] <= 5],
            'k10': df[df['train_freq'] <= 10],
            'warm': df[df['train_freq'] > 10]
        }
        
        for g_name, g_df in cold_start_groups.items():
            if len(g_df) == 0:
                continue
            g_y_true = g_df['y_true'].values.astype(int)
            g_p_pred = g_df['p_pred'].values.astype(float)
            
            g_auc, g_acc, g_nll, g_rmse = calculate_metrics(g_y_true, g_p_pred)
            g_ece = compute_ece(g_y_true, g_p_pred)
            g_brier, g_unc, g_rel, g_res = compute_brier_decomposition(g_y_true, g_p_pred)
            
            cold_start_rows.append({
                'dataset': dataset,
                'split_mode': split_mode,
                'model': model,
                'seed': seed,
                'group': g_name,
                'n_kcs': len(g_df['kc_id'].unique()),
                'n_events': len(g_df),
                'auc': g_auc,
                'acc': g_acc,
                'nll': g_nll,
                'rmse': g_rmse,
                'ece': g_ece,
                'brier': g_brier,
                'reliability': g_rel,
                'resolution': g_res
            })
            
    # Convert to DataFrames
    df_clean_overall = pd.DataFrame(overall_rows)
    df_clean_bucket = pd.DataFrame(bucket_rows)
    df_clean_cold_start = pd.DataFrame(cold_start_rows)
    
    # Save raw clean files
    out_dir = Path("results/tables")
    df_clean_overall.to_csv(out_dir / "clean_overall_results.csv", index=False)
    df_clean_bucket.to_csv(out_dir / "clean_metric_per_bucket.csv", index=False)
    df_clean_cold_start.to_csv(out_dir / "clean_cold_start_results.csv", index=False)
    
    # Save sensitivity analysis clean file (just filter raw sensitivity)
    sens_path = out_dir / "sensitivity_analysis.csv"
    if sens_path.exists():
        df_sens = pd.read_csv(sens_path)
        df_clean_sens = df_sens[df_sens['dataset'].isin(['assist2012', 'junyi', 'xes3g5m'])]
        df_clean_sens = df_clean_sens[df_clean_sens['model'].isin(['bkt', 'dkt', 'simplekt'])]
        df_clean_sens.to_csv(out_dir / "clean_sensitivity_analysis.csv", index=False)
    
    # 3. Create Summaries (mean and std across seeds)
    def make_summary(df, group_cols, numeric_cols):
        grouped = df.groupby(group_cols)
        mean_df = grouped[numeric_cols].mean()
        std_df = grouped[numeric_cols].std()
        
        summary = mean_df.copy()
        for col in numeric_cols:
            summary[f"{col}_mean"] = mean_df[col]
            summary[f"{col}_std"] = std_df[col].fillna(0.0)
            summary = summary.drop(columns=[col])
        return summary.reset_index()

    print("Generating summaries...")
    
    df_summary_overall = make_summary(df_clean_overall, ['dataset', 'split_mode', 'model'], ['auc', 'acc', 'nll', 'rmse'])
    df_summary_overall.to_csv(out_dir / "clean_overall_results_summary.csv", index=False)
    
    df_summary_bucket = make_summary(df_clean_bucket, ['dataset', 'split_mode', 'model', 'bucket'], 
                                     ['auc', 'acc', 'nll', 'rmse', 'ece', 'brier', 'uncertainty', 'reliability', 'resolution'])
    df_summary_bucket.to_csv(out_dir / "clean_metric_per_bucket_summary.csv", index=False)
    
    # Save merged calibration by bucket file
    df_clean_calib = df_summary_bucket[['dataset', 'split_mode', 'model', 'bucket', 'ece_mean', 'ece_std', 'brier_mean', 'brier_std', 'uncertainty_mean', 'reliability_mean', 'resolution_mean']]
    df_clean_calib.to_csv(out_dir / "clean_calibration_by_bucket.csv", index=False)
    
    df_summary_cold_start = make_summary(df_clean_cold_start, ['dataset', 'split_mode', 'model', 'group'], 
                                         ['auc', 'acc', 'ece', 'brier', 'reliability', 'resolution'])
    df_summary_cold_start.to_csv(out_dir / "clean_cold_start_results_summary.csv", index=False)
    
    print("Recalculation Complete! Clean data files successfully created in results/tables/")

if __name__ == "__main__":
    main()
