import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import os

def plot_reliability_diagram(dataset, model, bucket, bin_df, ece_val, n_events, output_path):
    """Plots a single reliability diagram."""
    plt.figure(figsize=(6, 6))
    
    # Filter bins for this specific plot
    df = bin_df[(bin_df['dataset'] == dataset) & 
                (bin_df['model'] == model) & 
                (bin_df['bucket'] == bucket)]
    
    if df.empty:
        print(f"No bin data for {dataset} {model} {bucket}")
        return

    # Sort by bin_id
    df = df.sort_values('bin_id')
    
    # 1. Main Plot: Accuracy vs Confidence
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfectly Calibrated')
    
    # Plot only bins with samples
    valid_bins = df[df['n_bin'] > 0]
    plt.plot(valid_bins['conf_bin'], valid_bins['acc_bin'], marker='o', linewidth=2, color='blue', label='Model')
    
    # Bars for gaps
    plt.bar(valid_bins['conf_bin'], valid_bins['acc_bin'], width=0.05, alpha=0.2, color='blue', edgecolor='blue')
    
    plt.title(f"Reliability Diagram: {model} ({bucket})\nDataset: {dataset} | ECE: {ece_val:.4f} | N: {n_events}")
    plt.xlabel("Predicted Confidence")
    plt.ylabel("Empirical Accuracy")
    plt.ylim(0, 1)
    plt.xlim(0, 1)
    plt.legend(loc='upper left')
    plt.grid(alpha=0.3)
    
    # 2. Inset or secondary axis for bin distribution? 
    # Let's add a histogram at the bottom
    ax2 = plt.axes([0.65, 0.2, 0.2, 0.2]) # [left, bottom, width, height]
    ax2.bar(df['bin_id'], df['n_bin'], color='gray', alpha=0.5)
    ax2.set_xticks([])
    ax2.set_title("Bin Counts", fontsize=8)
    
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="Generate reliability diagrams.")
    parser.add_argument("--bin_path", type=str, default="results/tables/ece_per_bucket_bins.csv")
    parser.add_argument("--ece_path", type=str, default="results/tables/ece_per_bucket.csv")
    args = parser.parse_args()
    
    bin_path = Path(args.bin_path)
    ece_path = Path(args.ece_path)
    
    if not bin_path.exists() or not ece_path.exists():
        print("Required CSV files for plotting not found.")
        return
        
    df_bins = pd.read_csv(bin_path)
    df_ece = pd.read_csv(ece_path)
    
    fig_dir = Path("results/figures/reliability_per_bucket")
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # We plot for the first seed (e.g. 42) to avoid clutter, or average?
    # Usually we plot for a representative run. Let's use seed 42.
    df_ece_seed = df_ece[df_ece['seed'] == 42]
    
    print(f"Generating reliability diagrams for seed 42...")
    
    for _, row in df_ece_seed.iterrows():
        dataset = row['dataset']
        model = row['model']
        bucket = row['bucket']
        mode = row['split_mode']
        ece_val = row['ece']
        n_events = row['n_events']
        
        fname = f"{dataset}_{mode}_{model}_{bucket}.pdf"
        output_path = fig_dir / fname
        
        plot_reliability_diagram(dataset, model, bucket, df_bins[df_bins['seed'] == 42], ece_val, n_events, output_path)
        
    print(f"Reliability diagrams saved to {fig_dir}")

if __name__ == "__main__":
    main()
