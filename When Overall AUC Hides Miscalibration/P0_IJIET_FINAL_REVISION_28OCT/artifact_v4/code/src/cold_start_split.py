import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import glob
from src.metrics import compute_metrics
from src.calibration_eval import compute_ece
from src.brier_decomposition import compute_brier_decomposition

def main():
    parser = argparse.ArgumentParser(description="Evaluate cold-start concept groups.")
    parser.add_argument("--prediction_dir", type=str, default="results/predictions")
    parser.add_argument("--strata_path", type=str, default="results/tables/kc_strata.csv")
    args = parser.parse_args()
    
    pred_dir = Path(args.prediction_dir)
    strata_path = Path(args.strata_path)
    
    if not pred_dir.exists() or not strata_path.exists():
        print("Required files for cold-start evaluation not found.")
        return
        
    strata_df = pd.read_csv(strata_path)
    pred_files = glob.glob(str(pred_dir / "*.csv"))
    
    results = []
    feasibility = []
    
    print(f"Processing {len(pred_files)} prediction files for cold-start diagnostics...")
    
    for f in pred_files:
        df = pd.read_csv(f)
        if df.empty: continue
        
        groups = df.groupby(['dataset', 'split_mode', 'model', 'seed'])
        for name, group in groups:
            dataset, mode, model, seed = name
            
            # Filter strata for this experiment to get train_freq
            exp_strata = strata_df[(strata_df['dataset'] == dataset) & 
                                   (strata_df['split'] == mode) & 
                                   (strata_df['fold'] == (group['seed'].map({42:0, 123:1, 2026:2}).iloc[0] if mode == 'learner_based' else 0))]
            
            if exp_strata.empty: continue
            
            kc_to_freq = exp_strata.set_index('kc_id')['train_freq'].to_dict()
            group = group.copy()
            group['train_freq'] = group['kc_id'].map(kc_to_freq)
            
            # Definitions
            # strict: freq == 0
            # limited k=5: freq <= 5
            # limited k=10: freq <= 10
            # warm: freq > 10
            
            conditions = {
                "strict": group['train_freq'] == 0,
                "k5": group['train_freq'] <= 5,
                "k10": group['train_freq'] <= 10,
                "warm": group['train_freq'] > 10
            }
            
            # Log feasibility (sample sizes)
            for k_label, mask in conditions.items():
                feasibility.append({
                    "dataset": dataset, "split_mode": mode, "model": model, "seed": seed,
                    "group": k_label, "n_events": mask.sum(), "n_kcs": group[mask]['kc_id'].nunique()
                })
                
                # Compute all metrics
                sub = group[mask]
                if len(sub) > 0:
                    m = compute_metrics(sub['y_true'].values, sub['p_pred'].values)
                    ece, _, _, _, _ = compute_ece(sub['y_true'].values, sub['p_pred'].values)
                    bs, unc, rel, res = compute_brier_decomposition(sub['y_true'].values, sub['p_pred'].values)
                    
                    results.append({
                        "dataset": dataset, "split_mode": mode, "model": model, "seed": seed,
                        "group": k_label, "n_events": len(sub),
                        "auc": m['auc'], "acc": m['acc'], "nll": m['nll'],
                        "ece": ece, "brier": bs, "reliability": rel, "resolution": res
                    })

    # Save results
    out_dir = Path("results/tables")
    pd.DataFrame(results).to_csv(out_dir / "cold_start_results.csv", index=False)
    pd.DataFrame(feasibility).to_csv(out_dir / "cold_start_feasibility.csv", index=False)
    print(f"Cold-start evaluation complete. Results saved to {out_dir}")

if __name__ == "__main__":
    main()
