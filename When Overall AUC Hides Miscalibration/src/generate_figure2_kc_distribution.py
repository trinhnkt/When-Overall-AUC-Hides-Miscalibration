#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def main():
    # Load the distribution data
    dist_path = "results/tables/bucket_distribution.csv"
    if not os.path.exists(dist_path):
        print(f"Error: {dist_path} does not exist.")
        return
        
    df = pd.read_csv(dist_path)
    
    # Filter for the 3 official datasets and fold 0
    official_datasets = ['assist2012', 'junyi', 'xes3g5m']
    df_filtered = df[(df['dataset'].isin(official_datasets)) & (df['fold'] == 0)].copy()
    
    # Set up subplots (1 row, 3 columns)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=False)
    
    dataset_titles = {
        'assist2012': 'ASSISTments 2012',
        'junyi': 'Junyi Academy',
        'xes3g5m': 'XES3G5M'
    }
    
    buckets_order = ['strict_cold_start', 'very_sparse', 'sparse', 'medium', 'dense']
    split_colors = {
        'learner_based': '#2980B9', # Soft blue
        'temporal': '#E67E22'       # Soft orange
    }
    
    for i, dataset in enumerate(official_datasets):
        ax = axes[i]
        df_ds = df_filtered[df_filtered['dataset'] == dataset]
        
        # Complete missing combinations with 0
        records = []
        for split in ['learner_based', 'temporal']:
            for bucket in buckets_order:
                matching = df_ds[(df_ds['split'] == split) & (df_ds['bucket'] == bucket)]
                n_kcs = matching['n_kcs'].values[0] if not matching.empty else 0
                records.append({
                    'split': split,
                    'bucket': bucket,
                    'n_kcs': n_kcs
                })
        df_plot = pd.DataFrame(records)
        
        # Pivot for plotting
        df_pivot = df_plot.pivot(index='bucket', columns='split', values='n_kcs')
        df_pivot = df_pivot.reindex(buckets_order)
        
        # Plot
        df_pivot.plot(kind='bar', ax=ax, color=[split_colors['learner_based'], split_colors['temporal']], width=0.7)
        
        # Labels and formatting
        ax.set_title(dataset_titles[dataset], fontsize=13, fontweight='bold', pad=10)
        ax.set_ylabel("Number of KCs", fontsize=11)
        ax.set_xlabel("KC Strata", fontsize=11)
        ax.set_xticklabels(['Strict\n(=0)', 'V. Sparse\n(1-19)', 'Sparse\n(20-99)', 'Medium\n(100-499)', 'Dense\n(>=500)'], rotation=0, fontsize=9.5)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        ax.legend().remove()
        
    # Add a single shared legend at the top
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, ['Learner-based', 'Temporal'], loc='upper center', bbox_to_anchor=(0.5, 0.99), ncol=2, fontsize=12)
    
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    
    # Save the plots
    fig_dir = Path("paper/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to both requested locations for compatibility
    plt.savefig(fig_dir / "figure2_bucket_distribution.pdf", bbox_inches="tight", format="pdf", dpi=300)
    plt.savefig(fig_dir / "figure2_bucket_distribution.png", bbox_inches="tight", format="png", dpi=300)
    plt.savefig(fig_dir / "figure2_kc_bucket_distribution.pdf", bbox_inches="tight", format="pdf", dpi=300)
    plt.savefig(fig_dir / "figure2_kc_bucket_distribution.png", bbox_inches="tight", format="png", dpi=300)
    
    # Also save in results/figures
    results_fig_dir = Path("results/figures")
    results_fig_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(results_fig_dir / "kc_bucket_distribution.pdf", bbox_inches="tight", format="pdf", dpi=300)
    plt.savefig(results_fig_dir / "figure2_kc_bucket_distribution.pdf", bbox_inches="tight", format="pdf", dpi=300)
    
    plt.close()
    print("Figure 2 bucket distribution plots successfully generated in all locations.")

if __name__ == '__main__':
    from pathlib import Path
    main()
