#!/usr/bin/env python3
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def main():
    # Set up figure (wider to prevent text overflow)
    fig, ax = plt.subplots(figsize=(7.5, 9.5))
    ax.axis('off')
    
    # Define styles (increased font sizes for readability, tighter box styles)
    font_title = dict(fontsize=11.5, fontweight='bold', color="#1A252C", family='sans-serif')
    font_body = dict(fontsize=9.8, color="#2C3E50", family='sans-serif')
    arrow_style = dict(arrowstyle="->", color="#34495E", lw=2, mutation_scale=15)
    
    # Draw blocks (widened to make text sit very close to borders)
    # Block 1: Input Data
    rect1 = patches.FancyBboxPatch((0.04, 0.855), 0.92, 0.09, boxstyle="round,pad=0.01", fc="#EBF5FB", ec="#2E86C1", lw=2)
    ax.add_patch(rect1)
    ax.text(0.5, 0.915, "1. Input Data & Normalization", ha='center', va='center', **font_title)
    ax.text(0.5, 0.88, "Raw KT Logs (ASSISTments 2012, Junyi, XES3G5M) $\\rightarrow$ Schema Standardization", ha='center', va='center', **font_body)
    
    # Arrow 1 -> 2
    ax.annotate("", xy=(0.5, 0.775), xytext=(0.5, 0.855), arrowprops=arrow_style)
    
    # Block 2: Splitting Cohorts
    rect2 = patches.FancyBboxPatch((0.04, 0.685), 0.92, 0.09, boxstyle="round,pad=0.01", fc="#FEF9E7", ec="#D4AC0D", lw=2)
    ax.add_patch(rect2)
    ax.text(0.5, 0.745, "2. Splitting & Stratification", ha='center', va='center', **font_title)
    ax.text(0.5, 0.71, "Learner-based / Temporal Splits $\\rightarrow$ Train-only KC-frequency Buckets", ha='center', va='center', **font_body)
    
    # Arrow 2 -> 3
    ax.annotate("", xy=(0.5, 0.605), xytext=(0.5, 0.685), arrowprops=arrow_style)
    
    # Block 3: Baseline Training
    rect3 = patches.FancyBboxPatch((0.04, 0.515), 0.92, 0.09, boxstyle="round,pad=0.01", fc="#E8F8F5", ec="#17A589", lw=2)
    ax.add_patch(rect3)
    ax.text(0.5, 0.575, "3. Baseline Evaluation", ha='center', va='center', **font_title)
    ax.text(0.5, 0.54, "Model Training (IRT, DKT, SimpleKT) $\\rightarrow$ Raw Prediction CSV Export", ha='center', va='center', **font_body)
    
    # Arrow 3 -> 4
    ax.annotate("", xy=(0.5, 0.445), xytext=(0.5, 0.515), arrowprops=arrow_style)
    
    # Block 4: Multi-dimensional Diagnostics
    rect4 = patches.FancyBboxPatch((0.02, 0.215), 0.96, 0.23, boxstyle="round,pad=0.01", fc="#F5EEF8", ec="#8E44AD", lw=2)
    ax.add_patch(rect4)
    ax.text(0.5, 0.415, "4. Diagnostic Metrics & Stratification Suite", ha='center', va='center', **font_title)
    
    ax.text(0.5, 0.37, "• Aggregate Metrics: AUC, Accuracy, NLL, RMSE", ha='center', va='center', **font_body)
    ax.text(0.5, 0.325, "• Calibration Strata: Expected Calibration Error (ECE) & Brier Decomposition", ha='center', va='center', **font_body)
    ax.text(0.5, 0.28, "• Visual Analytics: Multi-seed Reliability Diagrams per KC Bucket", ha='center', va='center', **font_body)
    ax.text(0.5, 0.235, "• Cold-start Subsets: Strict (f_train = 0), k-shot (f_train <= 5 or <= 10) & Warm", ha='center', va='center', **font_body)
    
    # Arrow 4 -> 5
    ax.annotate("", xy=(0.5, 0.145), xytext=(0.5, 0.215), arrowprops=arrow_style)
    
    # Block 5: Hygiene and Reporting
    rect5 = patches.FancyBboxPatch((0.04, 0.015), 0.92, 0.13, boxstyle="round,pad=0.01", fc="#FDEDEC", ec="#CB4335", lw=2)
    ax.add_patch(rect5)
    ax.text(0.5, 0.095, "5. Leakage & Predictive Sanity Audit (L1--L8)", ha='center', va='center', **font_title)
    ax.text(0.5, 0.045, "Automatically Generated Reports and Standardized LaTeX/PDF Artifacts", ha='center', va='center', **font_body)
    
    # Save as PDF
    os.makedirs("paper/figures", exist_ok=True)
    plt.savefig("paper/figures/figure1_pipeline.pdf", format="pdf", bbox_inches="tight", dpi=300)
    plt.savefig("paper/figures/figure1_pipeline.png", format="png", bbox_inches="tight", dpi=300)
    plt.close()
    print("Pipeline diagram figure1_pipeline.pdf and figure1_pipeline.png generated successfully.")

if __name__ == '__main__':
    main()
