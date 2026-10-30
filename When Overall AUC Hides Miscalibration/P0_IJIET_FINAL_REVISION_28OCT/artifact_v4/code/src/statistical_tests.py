import pandas as pd
import numpy as np
from scipy.stats import wilcoxon
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run statistical tests.")
    parser.add_argument("--results_path", type=str, default="results/tables/overall_results.csv")
    args = parser.parse_args()
    
    results_path = Path(args.results_path)
    if not results_path.exists():
        print("Results file not found.")
        return
        
    df = pd.read_csv(results_path)
    if df.empty: return
    
    # Compare models (e.g. BKT vs DKT, etc.)
    # For each dataset and split_mode
    models = df['model'].unique()
    test_results = []
    
    for dataset in df['dataset'].unique():
        for mode in df['split_mode'].unique():
            sub = df[(df['dataset'] == dataset) & (df['split_mode'] == mode)]
            
            # Pairwise comparison
            for i in range(len(models)):
                for j in range(i + 1, len(models)):
                    m1, m2 = models[i], models[j]
                    
                    for metric in ['auc', 'ece', 'nll', 'rmse']:
                        if metric not in sub.columns and metric != 'ece': continue
                        
                        # If ECE is not in overall_results, we might need to load ece_per_bucket
                        # For now, let's assume we use what's in overall_results
                        # Wait, overall_results has AUC, ACC, NLL, RMSE.
                        # Let's add ECE if we can.
                        
                        # Load values across seeds
                        v1 = sub[sub['model'] == m1].sort_values('seed')[metric].values
                        v2 = sub[sub['model'] == m2].sort_values('seed')[metric].values
                        
                        if len(v1) == len(v2) and len(v1) >= 3:
                            try:
                                stat, p = wilcoxon(v1, v2)
                            except:
                                p = np.nan
                                
                            test_results.append({
                                "dataset": dataset, "split_mode": mode,
                                "model_1": m1, "model_2": m2,
                                "metric": metric, "p_value": p,
                                "mean_1": np.mean(v1), "mean_2": np.mean(v2)
                            })

    pd.DataFrame(test_results).to_csv("results/tables/statistical_tests.csv", index=False)
    print("Statistical tests complete. Saved to results/tables/statistical_tests.csv")

if __name__ == "__main__":
    main()
