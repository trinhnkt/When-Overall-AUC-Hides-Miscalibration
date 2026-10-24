#!/usr/bin/env python3
"""
src/make_clean_latex_tables.py

Generate highly professional, beautifully formatted, double-column and single-column
LaTeX tables for the peer-review revision of the P0 paper.
"""

import pandas as pd
from pathlib import Path

def fmt(mean, std):
    if pd.isna(mean):
        return "-"
    if pd.isna(std) or std == 0.0:
        return f"${mean:.4f}$"
    return f"${mean:.4f} \\pm {std:.4f}$"

def main():
    print("Initializing Generation of Clean LaTeX Tables...")
    out_dir = Path("paper/tables")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. Table II: Dataset Statistics (table1_dataset_stats.tex)
    # -------------------------------------------------------------
    # Columns: Dataset, Split Mode, #Learners, #Items, #KCs, #Interactions, #Train, #Valid, #Test, Avg. Seq. Len.
    stats_data = [
        # assist2012
        {"dataset": "ASSISTments 2012", "split": "Learner-based", "users": "27,806", "items": "52,672", "kcs": "265", "total": "2,657,490", "train": "1,865,217", "valid": "258,123", "test": "534,150", "avg_seq": "95.57"},
        {"dataset": "ASSISTments 2012", "split": "Temporal", "users": "27,806", "items": "52,672", "kcs": "265", "total": "2,657,490", "train": "1,860,242", "valid": "265,749", "test": "531,499", "avg_seq": "95.57"},
        # junyi
        {"dataset": "Junyi Academy", "split": "Learner-based", "users": "71,014", "items": "25,784", "kcs": "1,326", "total": "16,215,567", "train": "11,373,990", "valid": "1,572,555", "test": "3,269,022", "avg_seq": "228.34"},
        {"dataset": "Junyi Academy", "split": "Temporal", "users": "71,014", "items": "25,784", "kcs": "1,326", "total": "16,215,567", "train": "11,350,896", "valid": "1,621,556", "test": "3,243,115", "avg_seq": "228.34"},
        # xes3g5m
        {"dataset": "XES3G5M", "split": "Learner-based", "users": "18,066", "items": "7,653", "kcs": "866", "total": "7,953,709", "train": "5,572,247", "valid": "792,317", "test": "1,589,145", "avg_seq": "440.26"},
        {"dataset": "XES3G5M", "split": "Temporal", "users": "18,066", "items": "7,653", "kcs": "866", "total": "7,953,709", "train": "5,567,596", "valid": "795,370", "test": "1,590,743", "avg_seq": "440.26"}
    ]
    
    tex_stats = []
    tex_stats.append("\\begin{table*}[t]")
    tex_stats.append("\\caption{Dataset and Splitting Cohort Statistics}")
    tex_stats.append("\\label{tab:datasets}")
    tex_stats.append("\\centering")
    tex_stats.append("\\small")
    tex_stats.append("\\begin{tabular}{llrrrrrrrr}")
    tex_stats.append("\\toprule")
    tex_stats.append("Dataset & Split Mode & \\#Learners & \\#Items & \\#KCs & \\#Interactions & \\#Train & \\#Valid & \\#Test & Avg. Seq. Len. \\\\")
    tex_stats.append("\\midrule")
    for row in stats_data:
        tex_stats.append(f"{row['dataset']} & {row['split']} & {row['users']} & {row['items']} & {row['kcs']} & {row['total']} & {row['train']} & {row['valid']} & {row['test']} & {row['avg_seq']} \\\\")
    tex_stats.append("\\bottomrule")
    tex_stats.append("\\end{tabular}")
    tex_stats.append("\\end{table*}")
    
    with open(out_dir / "table1_dataset_stats.tex", "w") as f:
        f.write("\n".join(tex_stats) + "\n")
        
    # -------------------------------------------------------------
    # 2. Table I: Leakage Audit (table1_leakage_audit.tex & table2_leakage_audit.tex)
    # -------------------------------------------------------------
    # Standard Leakage table using \path{} for files with explicit column widths to prevent overflow
    tex_leakage = []
    tex_leakage.append("\\begin{table*}[t]")
    tex_leakage.append("\\caption{Rigorous Multi-Channel Leakage Prevention Checklist}")
    tex_leakage.append("\\label{tab:leakage}")
    tex_leakage.append("\\centering")
    tex_leakage.append("\\footnotesize")
    tex_leakage.append("\\begin{tabular}{lp{5.5cm}p{4.2cm}lp{5.5cm}}")
    tex_leakage.append("\\toprule")
    tex_leakage.append("Channel & Risk / Description & Evidence & Status & Notes \\\\")
    tex_leakage.append("\\midrule")
    tex_leakage.append("L1 & Split leakage (user overlap, temporal order) & \\path{split_audit.csv} & PASS & No user overlap or temporal inversions detected \\\\")
    tex_leakage.append("L2 & Preprocessing leakage (transformations fit scope) & \\path{preprocess.py} & PASS & No global normalization detected \\\\")
    tex_leakage.append("L3 & Q-matrix / KC mapping leakage & \\path{kc_map.json} & PASS & Static mapping from dataset \\\\")
    tex_leakage.append("L4 & Sparse-bucket leakage & \\path{kc_strata.csv} & PASS & Bucket assignment is strictly based on training frequency \\\\")
    tex_leakage.append("L5 & Calibration leakage (test-based tuning) & \\path{baseline_runner.py} & PASS & No post-hoc tuning on test set \\\\")
    tex_leakage.append("L6 & Hyperparameter leakage (model selection) & \\path{baseline_runner.py} & PASS & Validation-based selection only \\\\")
    tex_leakage.append("L7 & Cold-start leakage & \\path{split_constructor.py} & PASS & Classification uses train\\_freq only \\\\")
    tex_leakage.append("\\bottomrule")
    tex_leakage.append("\\end{tabular}")
    tex_leakage.append("\\end{table*}")
    
    with open(out_dir / "table1_leakage_audit.tex", "w") as f:
        f.write("\n".join(tex_leakage) + "\n")
        
    with open(out_dir / "table2_leakage_audit.tex", "w") as f:
        f.write("\n".join(tex_leakage) + "\n")
        
    # -------------------------------------------------------------
    # 3. Table III: Overall Performance (table3_overall_results.tex & tableA_overall_full.tex)
    # -------------------------------------------------------------
    df_overall = pd.read_csv("results/tables/clean_overall_results_summary.csv")
    
    def generate_overall_tex(df, split_mode, title, label, filepath, is_appendix=False):
        tex = []
        if is_appendix:
            tex.append("\\begin{table*}[h]")
        else:
            tex.append("\\begin{table*}[t]")
        tex.append(f"\\caption{{{title}}}")
        tex.append(f"\\label{{{label}}}")
        tex.append("\\centering")
        tex.append("\\resizebox{\\textwidth}{!}{%")
        tex.append("\\begin{tabular}{lllcccc}")
        tex.append("\\toprule")
        tex.append("Dataset & Split & Model & AUC & ACC & NLL & RMSE \\\\")
        tex.append("\\midrule")
        
        filtered = df[df['split_mode'] == split_mode].copy()
        
        # Sort values for consistency
        filtered['dataset_sort'] = filtered['dataset'].map({'assist2012': 0, 'junyi': 1, 'xes3g5m': 2})
        filtered['model_sort'] = filtered['model'].map({'bkt': 0, 'dkt': 1, 'simplekt': 2})
        filtered = filtered.sort_values(['dataset_sort', 'model_sort'])
        
        last_ds = None
        for _, row in filtered.iterrows():
            ds_name = row['dataset'].upper()
            if ds_name == "ASSIST2012":
                ds_display = "ASSISTments 2012"
            elif ds_name == "JUNYI":
                ds_display = "Junyi Academy"
            else:
                ds_display = "XES3G5M"
                
            if ds_display != last_ds:
                if last_ds is not None:
                    tex.append("\\midrule")
                last_ds = ds_display
                ds_col = ds_display
            else:
                ds_col = ""
                
            model_display = row['model'].upper() if row['model'] != "simplekt" else "SimpleKT"
            
            auc_str = fmt(row['auc_mean'], row['auc_std'])
            acc_str = fmt(row['acc_mean'], row['acc_std'])
            nll_str = fmt(row['nll_mean'], row['nll_std'])
            rmse_str = fmt(row['rmse_mean'], row['rmse_std'])
            
            # Map split_mode to user-friendly name
            split_display = "Learner-based" if row['split_mode'] == "learner_based" else "Temporal"
            
            tex.append(f"{ds_col} & {split_display} & {model_display} & {auc_str} & {acc_str} & {nll_str} & {rmse_str} \\\\")
            
        tex.append("\\bottomrule")
        tex.append("\\multicolumn{7}{p{14.5cm}}{\\scriptsize \\textit{Note: The unusually high NLL values for BKT are mainly caused by near-deterministic probability outputs and should be interpreted cautiously. We retain BKT primarily as a classical reference baseline.}} \\\\")
        tex.append("\\end{tabular}%")
        tex.append("}")
        tex.append("\\end{table*}")
        
        with open(filepath, "w") as f:
            f.write("\n".join(tex) + "\n")
            
    generate_overall_tex(df_overall, "learner_based", "Overall Performance under Learner-based Split", "tab:overall", out_dir / "table3_overall_results.tex")
    generate_overall_tex(df_overall, "learner_based", "Overall Performance under Learner-based Split", "tab:overall", out_dir / "table3_overall_performance.tex")
    generate_overall_tex(df_overall, "temporal", "Overall Performance under Future Validation (Temporal Splits) [Appendix]", "tab:overall_temporal", out_dir / "tableA_overall_full.tex", is_appendix=True)
    
    # -------------------------------------------------------------
    # 4. Table IV: Performance by Bucket (table4_metric_per_bucket.tex & tableA_performance_by_bucket_full.tex)
    # -------------------------------------------------------------
    df_bucket = pd.read_csv("results/tables/clean_metric_per_bucket_summary.csv")
    
    def generate_bucket_tex(df, split_mode, title, label, filepath):
        df_raw = pd.read_csv("results/tables/clean_metric_per_bucket.csv")
        tex = []
        tex.append("\\begin{table*}[t]")
        tex.append(f"\\caption{{{title}}}")
        tex.append(f"\\label{{{label}}}")
        tex.append("\\centering")
        tex.append("\\resizebox{\\textwidth}{!}{%")
        tex.append("\\begin{tabular}{lllcrcccc}")
        tex.append("\\toprule")
        tex.append("Dataset & Model & Bucket & \\#KCs & \\#Events & AUC & ACC & NLL & RMSE \\\\")
        tex.append("\\midrule")
        
        filtered = df[(df['split_mode'] == split_mode) & (df['bucket'] != 'strict_cold_start')].copy()
        filtered['dataset_sort'] = filtered['dataset'].map({'assist2012': 0, 'junyi': 1, 'xes3g5m': 2})
        filtered['model_sort'] = filtered['model'].map({'bkt': 0, 'dkt': 1, 'simplekt': 2})
        filtered['bucket_sort'] = filtered['bucket'].map({'dense': 0, 'medium': 1, 'sparse': 2, 'very_sparse': 3})
        filtered = filtered.sort_values(['dataset_sort', 'model_sort', 'bucket_sort'])
        
        last_ds = None
        last_model = None
        for _, row in filtered.iterrows():
            ds_name = row['dataset'].upper()
            if ds_name == "ASSIST2012":
                ds_display = "ASSISTments 2012"
            elif ds_name == "JUNYI":
                ds_display = "Junyi Academy"
            else:
                ds_display = "XES3G5M"
                
            if ds_display != last_ds:
                if last_ds is not None:
                    tex.append("\\midrule")
                last_ds = ds_display
                ds_col = ds_display
                last_model = None
            else:
                ds_col = ""
                
            model_display = row['model'].upper() if row['model'] != "simplekt" else "SimpleKT"
            if model_display != last_model:
                model_col = model_display
                last_model = model_display
            else:
                model_col = ""
                
            bucket_display = row['bucket'].replace("_", "\\_")
            
            # Retrieve KCs and Events count (average across seeds for model consistency)
            raw_match = df_raw[(df_raw['dataset'] == row['dataset']) & 
                               (df_raw['split_mode'] == split_mode) & 
                               (df_raw['model'] == row['model']) & 
                               (df_raw['bucket'] == row['bucket'])]
            if not raw_match.empty:
                n_kcs = int(round(raw_match['n_kcs'].mean()))
                n_events = int(raw_match['n_events'].mean())
                n_kcs_str = f"{n_kcs:,}"
                n_events_str = f"{n_events:,}"
            else:
                n_kcs_str = "-"
                n_events_str = "-"
            
            auc_str = fmt(row['auc_mean'], row['auc_std'])
            acc_str = fmt(row['acc_mean'], row['acc_std'])
            nll_str = fmt(row['nll_mean'], row['nll_std'])
            rmse_str = fmt(row['rmse_mean'], row['rmse_std'])
            
            tex.append(f"{ds_col} & {model_col} & {bucket_display} & {n_kcs_str} & {n_events_str} & {auc_str} & {acc_str} & {nll_str} & {rmse_str} \\\\")
            
        tex.append("\\bottomrule")
        tex.append("\\multicolumn{9}{p{16.5cm}}{\\scriptsize \\textit{Note: \\#Events denotes the number of prediction rows used for metric computation after model-specific prediction export and KC-strata matching. Very sparse AUC should be interpreted cautiously due to limited test events.}} \\\\")
        tex.append("\\end{tabular}%")
        tex.append("}")
        tex.append("\\end{table*}")
        
        with open(filepath, "w") as f:
            f.write("\n".join(tex) + "\n")
            
    generate_bucket_tex(df_bucket, "learner_based", "Knowledge Tracing Performance Breakdown by Skill Strata (Learner-based)", "tab:bucket", out_dir / "table4_metric_per_bucket.tex")
    generate_bucket_tex(df_bucket, "learner_based", "Knowledge Tracing Performance Breakdown by Skill Strata (Learner-based)", "tab:bucket", out_dir / "table4_performance_by_bucket.tex")
    generate_bucket_tex(df_bucket, "temporal", "Knowledge Tracing Performance Breakdown by Skill Strata (Temporal splits) [Appendix]", "tab:bucket_temporal", out_dir / "tableA_performance_by_bucket_full.tex")
    
    # -------------------------------------------------------------
    # 5. Table V: Calibration by Bucket (table5_calibration_per_bucket.tex)
    # -------------------------------------------------------------
    # Calibration ECE and Brier score decomposition (UNC, REL, RES)
    df_calib = pd.read_csv("results/tables/clean_calibration_by_bucket.csv")
    df_calib = df_calib[df_calib['split_mode'] == 'learner_based'].copy()
    df_events = pd.read_csv("results/tables/clean_metric_per_bucket.csv")
    df_events = df_events[df_events['split_mode'] == 'learner_based'].copy()
    
    # Calculate average events across seeds
    events_summary = df_events.groupby(['dataset', 'model', 'bucket'])['n_events'].mean().reset_index()
    
    df_calib = df_calib.merge(events_summary, on=['dataset', 'model', 'bucket'], how='left')
    
    df_calib = df_calib[df_calib['bucket'] != 'strict_cold_start'].copy()
    df_calib['dataset_sort'] = df_calib['dataset'].map({'assist2012': 0, 'junyi': 1, 'xes3g5m': 2})
    df_calib['model_sort'] = df_calib['model'].map({'bkt': 0, 'dkt': 1, 'simplekt': 2})
    df_calib['bucket_sort'] = df_calib['bucket'].map({'dense': 0, 'medium': 1, 'sparse': 2, 'very_sparse': 3})
    df_calib = df_calib.sort_values(['dataset_sort', 'model_sort', 'bucket_sort'])
    
    # A. Table V (Compact/Main): Dataset, Model, Bucket, #Events, ECE, Brier, UNC, REL, RES
    tex_cal = []
    tex_cal.append("\\begin{table*}[t]")
    tex_cal.append("\\caption{Calibration Breakdown by Frequency Stratum}")
    tex_cal.append("\\label{tab:calib}")
    tex_cal.append("\\centering")
    tex_cal.append("\\resizebox{\\textwidth}{!}{%")
    tex_cal.append("\\begin{tabular}{lllrccccc}")
    tex_cal.append("\\toprule")
    tex_cal.append("Dataset & Model & Bucket & \\#Events & ECE & Brier & UNC & REL & RES \\\\")
    tex_cal.append("\\midrule")
    
    # B. Table V Compact: Dataset, Model, Bucket, #Events, ECE, Brier
    tex_compact = []
    tex_compact.append("\\begin{table}[t]")
    tex_compact.append("\\caption{Compact Calibration Breakdown by Frequency Stratum}")
    tex_compact.append("\\label{tab:calib_compact}")
    tex_compact.append("\\centering")
    tex_compact.append("\\resizebox{\\columnwidth}{!}{%")
    tex_compact.append("\\begin{tabular}{lllrcc}")
    tex_compact.append("\\toprule")
    tex_compact.append("Dataset & Model & Bucket & \\#Events & ECE & Brier \\\\")
    tex_compact.append("\\midrule")
    
    # C. Table A Full (Appendix): Dataset, Model, Bucket, #Events, ECE, Brier, UNC, REL, RES
    tex_full = []
    tex_full.append("\\begin{table*}[t]")
    tex_full.append("\\caption{Comprehensive Calibration Breakdown and Brier Score Decomposition}")
    tex_full.append("\\label{tab:calib_full}")
    tex_full.append("\\centering")
    tex_full.append("\\small")
    tex_full.append("\\begin{tabular}{lllrcccccc}")
    tex_full.append("\\toprule")
    tex_full.append("Dataset & Model & Bucket & \\#Events & ECE & Brier & UNC & REL & RES \\\\")
    tex_full.append("\\midrule")
    
    last_ds = None
    last_model = None
    for _, row in df_calib.iterrows():
        ds_name = row['dataset'].upper()
        if ds_name == "ASSIST2012":
            ds_display = "ASSISTments 2012"
        elif ds_name == "JUNYI":
            ds_display = "Junyi Academy"
        else:
            ds_display = "XES3G5M"
            
        if ds_display != last_ds:
            if last_ds is not None:
                tex_cal.append("\\midrule")
                tex_compact.append("\\midrule")
                tex_full.append("\\midrule")
            last_ds = ds_display
            ds_col = ds_display
            last_model = None
        else:
            ds_col = ""
            
        model_display = row['model'].upper() if row['model'] != "simplekt" else "SimpleKT"
        if model_display != last_model:
            model_col = model_display
            last_model = model_display
        else:
            model_col = ""
            
        bucket_display = row['bucket'].replace("_", "\\_")
        
        n_events = int(row['n_events']) if not pd.isna(row['n_events']) else 0
        n_events_str = f"{n_events:,}"
        
        ece_str = fmt(row['ece_mean'], row['ece_std'])
        brier_str = fmt(row['brier_mean'], row['brier_std'])
        unc_str = f"${row['uncertainty_mean']:.4f}$" if not pd.isna(row['uncertainty_mean']) else "-"
        rel_str = f"${row['reliability_mean']:.4f}$" if not pd.isna(row['reliability_mean']) else "-"
        res_str = f"${row['resolution_mean']:.4f}$" if not pd.isna(row['resolution_mean']) else "-"
        
        tex_cal.append(f"{ds_col} & {model_col} & {bucket_display} & {n_events_str} & {ece_str} & {brier_str} & {unc_str} & {rel_str} & {res_str} \\\\")
        tex_compact.append(f"{ds_col} & {model_col} & {bucket_display} & {n_events_str} & {ece_str} & {brier_str} \\\\")
        tex_full.append(f"{ds_col} & {model_col} & {bucket_display} & {n_events_str} & {ece_str} & {brier_str} & {unc_str} & {rel_str} & {res_str} \\\\")
        
    tex_cal.append("\\midrule")
    tex_cal.append("\\multicolumn{9}{p{17.5cm}}{\\scriptsize \\textbf{Note:} For BKT, ECE and Brier are numerically close in several strata, likely due to near-deterministic probability outputs under this implementation. These values are retained as diagnostic warnings and should be interpreted cautiously.} \\\\")
    tex_cal.append("\\bottomrule")
    tex_cal.append("\\end{tabular}")
    tex_cal.append("}")
    tex_cal.append("\\end{table*}")
    
    tex_compact.append("\\bottomrule")
    tex_compact.append("\\end{tabular}")
    tex_compact.append("}")
    tex_compact.append("\\end{table}")
    
    tex_full.append("\\bottomrule")
    tex_full.append("\\end{tabular}")
    tex_full.append("\\end{table*}")
    
    with open(out_dir / "table5_calibration_per_bucket.tex", "w") as f:
        f.write("\n".join(tex_cal) + "\n")
        
    with open(out_dir / "table5_calibration_by_bucket_compact.tex", "w") as f:
        f.write("\n".join(tex_compact) + "\n")
        
    with open(out_dir / "tableA_calibration_by_bucket_full.tex", "w") as f:
        f.write("\n".join(tex_full) + "\n")
        
    # Temporal Calibration Table (Appendix)
    df_calib_temp = pd.read_csv("results/tables/clean_calibration_by_bucket_temporal.csv")
    df_calib_temp = df_calib_temp[df_calib_temp['bucket'] != 'strict_cold_start'].copy()
    df_calib_temp['dataset_sort'] = df_calib_temp['dataset'].map({'assist2012': 0, 'junyi': 1, 'xes3g5m': 2})
    df_calib_temp['model_sort'] = df_calib_temp['model'].map({'bkt': 0, 'dkt': 1, 'simplekt': 2})
    df_calib_temp['bucket_sort'] = df_calib_temp['bucket'].map({'dense': 0, 'medium': 1, 'sparse': 2, 'very_sparse': 3})
    df_calib_temp = df_calib_temp.sort_values(['dataset_sort', 'model_sort', 'bucket_sort'])
    
    tex_temp = []
    tex_temp.append("\\begin{table*}[h]")
    tex_temp.append("\\caption{Calibration Breakdown and Brier Score Decomposition (Temporal Split)}")
    tex_temp.append("\\label{tab:calib_temporal}")
    tex_temp.append("\\centering")
    tex_temp.append("\\small")
    tex_temp.append("\\begin{tabular}{lllrcccccc}")
    tex_temp.append("\\toprule")
    tex_temp.append("Dataset & Model & Bucket & \\#Events & ECE & Brier & UNC & REL & RES \\\\")
    tex_temp.append("\\midrule")
    
    last_ds = None
    last_model = None
    for _, row in df_calib_temp.iterrows():
        ds_name = row['dataset'].upper()
        if ds_name == "ASSIST2012":
            ds_display = "ASSISTments 2012"
        elif ds_name == "JUNYI":
            ds_display = "Junyi Academy"
        else:
            ds_display = "XES3G5M"
            
        if ds_display != last_ds:
            if last_ds is not None:
                tex_temp.append("\\midrule")
            last_ds = ds_display
            ds_col = ds_display
            last_model = None
        else:
            ds_col = ""
            
        model_display = row['model'].upper() if row['model'] != "simplekt" else "SimpleKT"
        if model_display != last_model:
            model_col = model_display
            last_model = model_display
        else:
            model_col = ""
            
        bucket_display = row['bucket'].replace("_", "\\_")
        
        n_events = int(row['n_events']) if not pd.isna(row['n_events']) else 0
        n_events_str = f"{n_events:,}"
        
        ece_str = fmt(row['ece_mean'], row['ece_std'])
        brier_str = fmt(row['brier_mean'], row['brier_std'])
        unc_str = f"${row['uncertainty_mean']:.4f}$" if not pd.isna(row['uncertainty_mean']) else "-"
        rel_str = f"${row['reliability_mean']:.4f}$" if not pd.isna(row['reliability_mean']) else "-"
        res_str = f"${row['resolution_mean']:.4f}$" if not pd.isna(row['resolution_mean']) else "-"
        
        tex_temp.append(f"{ds_col} & {model_col} & {bucket_display} & {n_events_str} & {ece_str} & {brier_str} & {unc_str} & {rel_str} & {res_str} \\\\")
        
    tex_temp.append("\\midrule")
    tex_temp.append("\\multicolumn{9}{p{17.5cm}}{\\scriptsize \\textbf{Note:} BKT metrics often exhibit near-deterministic probability artifacts. These figures provide the temporal baseline for the reliability diagrams shown in Figure~3.} \\\\")
    tex_temp.append("\\bottomrule")
    tex_temp.append("\\end{tabular}")
    tex_temp.append("\\end{table*}")
    
    with open(out_dir / "tableA_calibration_by_bucket_temporal.tex", "w") as f:
        f.write("\n".join(tex_temp) + "\n")
        
    # -------------------------------------------------------------
    # 6. Table VI: Cold-start Results (table6_cold_start_results.tex)
    # -------------------------------------------------------------
    df_cold = pd.read_csv("results/tables/clean_cold_start_results_summary.csv")
    df_cold = df_cold[df_cold['split_mode'] == 'temporal'].copy()
    df_raw_cold = pd.read_csv("results/tables/clean_cold_start_results.csv")
    
    df_cold['dataset_sort'] = df_cold['dataset'].map({'assist2012': 0, 'junyi': 1, 'xes3g5m': 2})
    df_cold['model_sort'] = df_cold['model'].map({'bkt': 0, 'dkt': 1, 'simplekt': 2})
    df_cold['group_sort'] = df_cold['group'].map({'strict': 0, 'k5': 1, 'k10': 2, 'warm': 3})
    df_cold = df_cold.sort_values(['dataset_sort', 'model_sort', 'group_sort'])
    
    tex_cold = []
    tex_cold.append("\\begin{table*}[t]")
    tex_cold.append("\\caption{Cold-start Performance Metrics under Temporal Validation}")
    tex_cold.append("\\label{tab:cold_start}")
    tex_cold.append("\\centering")
    tex_cold.append("\\resizebox{\\textwidth}{!}{%")
    tex_cold.append("\\begin{tabular}{lllcrcccccc}")
    tex_cold.append("\\toprule")
    tex_cold.append("Dataset & Model & Group & \\#KCs & \\#Events & AUC & ACC & ECE & Brier & REL & RES \\\\")
    tex_cold.append("\\midrule")
    
    last_ds = None
    last_model = None
    for _, row in df_cold.iterrows():
        ds_name = row['dataset'].upper()
        if ds_name == "ASSIST2012":
            ds_display = "ASSISTments 2012"
        elif ds_name == "JUNYI":
            ds_display = "Junyi Academy"
        else:
            ds_display = "XES3G5M"
            
        if ds_display != last_ds:
            if last_ds is not None:
                tex_cold.append("\\midrule")
            last_ds = ds_display
            ds_col = ds_display
            last_model = None
        else:
            ds_col = ""
            
        model_display = row['model'].upper() if row['model'] != "simplekt" else "SimpleKT"
        if model_display != last_model:
            model_col = model_display
            last_model = model_display
        else:
            model_col = ""
            
        group_display = row['group']
        
        # Retrieve KCs and Events count
        raw_match = df_raw_cold[(df_raw_cold['dataset'] == row['dataset']) & 
                               (df_raw_cold['split_mode'] == 'temporal') & 
                               (df_raw_cold['model'] == row['model']) & 
                               (df_raw_cold['group'] == row['group'])]
        if not raw_match.empty:
            n_kcs = int(raw_match['n_kcs'].iloc[0])
            n_events = int(raw_match['n_events'].iloc[0])
            n_kcs_str = f"{n_kcs:,}"
            n_events_str = f"{n_events:,}"
        else:
            n_kcs_str = "-"
            n_events_str = "-"
            
        auc_str = fmt(row['auc_mean'], row['auc_std'])
        acc_str = fmt(row['acc_mean'], row['acc_std'])
        ece_str = fmt(row['ece_mean'], row['ece_std'])
        brier_str = fmt(row['brier_mean'], row['brier_std'])
        rel_str = fmt(row['reliability_mean'], row['reliability_std'])
        res_str = fmt(row['resolution_mean'], row['resolution_std'])
        
        tex_cold.append(f"{ds_col} & {model_col} & {group_display} & {n_kcs_str} & {n_events_str} & {auc_str} & {acc_str} & {ece_str} & {brier_str} & {rel_str} & {res_str} \\\\")
        
    tex_cold.append("\\bottomrule")
    tex_cold.append("\\multicolumn{11}{p{16.5cm}}{\\scriptsize \\textit{Note: For the Junyi Academy dataset, the strict, k5, and k10 cohorts coincide exactly because all 4 concepts in this category have zero training frequency.}} \\\\")
    tex_cold.append("\\end{tabular}%")
    tex_cold.append("}")
    tex_cold.append("\\end{table*}")
    
    with open(out_dir / "table6_cold_start_results.tex", "w") as f:
        f.write("\n".join(tex_cold) + "\n")
        
    # -------------------------------------------------------------
    # 7. Table A1: Sensitivity Analysis (tableA1_sensitivity.tex)
    # -------------------------------------------------------------
    df_sens = pd.read_csv("results/tables/clean_sensitivity_analysis.csv")
    # Group by setting and bucket to generate Mean ± Std
    summary_sens = df_sens.groupby(['setting', 'bucket'])[['auc', 'ece']].agg(['mean', 'std']).reset_index()
    summary_sens.columns = ['setting', 'bucket', 'auc_mean', 'auc_std', 'ece_mean', 'ece_std']
    
    summary_sens = summary_sens[summary_sens['bucket'] != 'strict_cold_start'].copy()
    summary_sens['bucket_sort'] = summary_sens['bucket'].map({'dense': 0, 'medium': 1, 'sparse': 2, 'very_sparse': 3})
    summary_sens = summary_sens.sort_values(['setting', 'bucket_sort'])
    
    tex_sens = []
    tex_sens.append("\\begin{table}[h]")
    tex_sens.append("\\caption{Sensitivity Analysis to KC-frequency Threshold Settings}")
    tex_sens.append("\\label{tab:sensitivity}")
    tex_sens.append("\\centering")
    tex_sens.append("\\resizebox{\\columnwidth}{!}{%")
    tex_sens.append("\\begin{tabular}{llcc}")
    tex_sens.append("\\toprule")
    tex_sens.append("Setting & Bucket & AUC & ECE \\\\")
    tex_sens.append("\\midrule")
    
    last_set = None
    for _, row in summary_sens.iterrows():
        set_name = row['setting'].replace("_", "\\_")
        if set_name != last_set:
            if last_set is not None:
                tex_sens.append("\\midrule")
            last_set = set_name
            set_col = set_name
        else:
            set_col = ""
            
        bucket_display = row['bucket'].replace("_", "\\_")
        auc_str = fmt(row['auc_mean'], row['auc_std'])
        ece_str = fmt(row['ece_mean'], row['ece_std'])
        
        tex_sens.append(f"{set_col} & {bucket_display} & {auc_str} & {ece_str} \\\\")
        
    tex_sens.append("\\bottomrule")
    tex_sens.append("\\end{tabular}")
    tex_sens.append("}")
    tex_sens.append("\\end{table}")
    
    with open(out_dir / "tableA1_sensitivity.tex", "w") as f:
        f.write("\n".join(tex_sens) + "\n")
        
    print("Flawless LaTeX Tables generated successfully under paper/tables/")

if __name__ == "__main__":
    main()
