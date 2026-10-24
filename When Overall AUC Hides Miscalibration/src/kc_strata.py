import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import os
import yaml

def get_bucket(freq):
    if freq == 0:
        return "strict_cold_start"
    elif freq < 20:
        return "very_sparse"
    elif freq < 100:
        return "sparse"
    elif freq < 500:
        return "medium"
    else:
        return "dense"

def process_dataset(dataset, config):
    seeds = config.get('seeds', [42, 123, 2026])
    modes = ['learner_based', 'temporal']
    
    all_strata = []
    
    for mode in modes:
        # For temporal, usually only fold_0. For learner, multiple folds.
        folds = range(len(seeds)) if mode == 'learner_based' else [0]
        
        for fold in folds:
            base_path = Path(f"data/processed/{dataset}/splits/{mode}/fold_{fold}")
            if not (base_path / "train.csv").exists(): continue
            
            print(f"[{dataset}] Processing strata for {mode} fold {fold}...")
            train = pd.read_csv(base_path / "train.csv")
            valid = pd.read_csv(base_path / "valid.csv")
            test = pd.read_csv(base_path / "test.csv")
            
            train_counts = train['kc_id'].value_counts().to_dict()
            valid_counts = valid['kc_id'].value_counts().to_dict()
            test_counts = test['kc_id'].value_counts().to_dict()
            
            all_kcs = sorted(set(train_counts.keys()) | set(valid_counts.keys()) | set(test_counts.keys()))
            
            for kc in all_kcs:
                tf = train_counts.get(kc, 0)
                vf = valid_counts.get(kc, 0)
                tef = test_counts.get(kc, 0)
                
                all_strata.append({
                    "dataset": dataset,
                    "split": mode,
                    "fold": fold,
                    "kc_id": kc,
                    "train_freq": tf,
                    "valid_freq": vf,
                    "test_freq": tef,
                    "bucket": get_bucket(tf) # Bucket ONLY based on train_freq
                })
                
    return pd.DataFrame(all_strata)

def main():
    parser = argparse.ArgumentParser(description="Stratify KCs by training frequency.")
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
        
    df_strata = process_dataset(args.dataset, config)
    if df_strata.empty:
        print("No data found to stratify.")
        return
        
    # Save kc_strata
    strata_path = Path("results/tables/kc_strata.csv")
    strata_path.parent.mkdir(parents=True, exist_ok=True)
    
    if strata_path.exists():
        df_old = pd.read_csv(strata_path)
        df_strata = pd.concat([df_old[df_old['dataset'] != args.dataset], df_strata], ignore_index=True)
    df_strata.to_csv(strata_path, index=False)
    
    # Save bucket distribution
    # We use the first fold of learner_based as the primary reference for the distribution table
    df_ref = df_strata[(df_strata['split'] == 'learner_based') & (df_strata['fold'] == 0)]
    if df_ref.empty:
        df_ref = df_strata.iloc[0:0] # Fallback if learner_based fold 0 missing
        
    dist = df_strata.groupby(['dataset', 'split', 'fold', 'bucket']).size().reset_index(name='n_kcs')
    dist_path = Path("results/tables/bucket_distribution.csv")
    dist.to_csv(dist_path, index=False)
    
    # Plot distribution (for the latest dataset processed)
    # Filter for fold 0
    df_plot = dist[(dist['dataset'] == args.dataset) & (dist['fold'] == 0)]
    if not df_plot.empty:
        plt.figure(figsize=(10, 6))
        # Pivot for easy plotting: mode as columns, bucket as index
        df_pivot = df_plot.pivot(index='bucket', columns='split', values='n_kcs')
        # Reorder buckets
        order = ['strict_cold_start', 'very_sparse', 'sparse', 'medium', 'dense']
        df_pivot = df_pivot.reindex(order)
        
        df_pivot.plot(kind='bar', ax=plt.gca())
        plt.title(f"KC Bucket Distribution - {args.dataset}")
        plt.ylabel("Number of KCs")
        plt.xlabel("Frequency Bucket")
        plt.xticks(rotation=0)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        fig_dir = Path("results/figures")
        fig_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(fig_dir / "kc_bucket_distribution.pdf")
        print(f"Plot saved to {fig_dir / 'kc_bucket_distribution.pdf'}")

if __name__ == "__main__":
    main()
