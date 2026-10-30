#!/usr/bin/env python3
"""
report_generator.py

Generate a Markdown diagnostic report and LaTeX paper tables for the P0 paper:
"Reproducible Sparse-Concept and Calibration Diagnostics for Knowledge Tracing"
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
import shutil
import os

import pandas as pd


# -----------------------------
# Utility functions
# -----------------------------

def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names for easier downstream handling."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def read_csv_if_exists(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    try:
        return normalize_cols(pd.read_csv(path))
    except Exception as exc:
        print(f"[WARN] Cannot read CSV: {path} | {exc}")
        return None


def read_first_available(paths: Iterable[Path]) -> tuple[Optional[pd.DataFrame], Optional[Path]]:
    for path in paths:
        df = read_csv_if_exists(path)
        if df is not None:
            return df, path
    return None, None


def relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def format_float(x) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, float):
        return f"{x:.4f}"
    return str(x)


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 25) -> str:
    """
    Convert DataFrame to a simple Markdown table without requiring tabulate.
    """
    if df is None or df.empty:
        return "_No data available._\n"

    shown = df.head(max_rows).copy()

    for col in shown.columns:
        if pd.api.types.is_float_dtype(shown[col]):
            shown[col] = shown[col].map(lambda v: "" if pd.isna(v) else f"{v:.4f}")
        else:
            shown[col] = shown[col].map(lambda v: "" if pd.isna(v) else str(v))

    cols = list(shown.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"

    rows = []
    for _, row in shown.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")

    table = "\n".join([header, sep] + rows)

    if len(df) > max_rows:
        table += f"\n\n_Showing first {max_rows} of {len(df)} rows._"

    return table + "\n"

def df_to_latex(df, path, caption="", label=""):
    """Saves a dataframe to a LaTeX table with booktabs style using Styler."""
    # In pandas 3.0, hide the index using hide(axis='index') before to_latex
    latex = df.style.hide(axis='index').to_latex(
        buf=None,
        caption=caption,
        label=label,
        hrules=True, # toprule, midrule, bottomrule
    )
    if "\\begin{table}" not in latex:
        latex = "\\begin{table}[ht]\n\\centering\n\\small\n" + latex + "\\end{table}"
    
    ensure_parent_dir(Path(path))
    with open(path, "w") as f:
        f.write(latex)
    print(f"Saved LaTeX table to {path}")

def summarize_numeric_by_group(
    df: pd.DataFrame,
    group_cols: list[str],
    metric_cols: list[str],
) -> pd.DataFrame:
    """
    Summarize metric columns by mean and std.
    """
    existing_group_cols = [c for c in group_cols if c in df.columns]
    existing_metric_cols = [c for c in metric_cols if c in df.columns]

    if not existing_group_cols or not existing_metric_cols:
        return df

    grouped = df.groupby(existing_group_cols, dropna=False)[existing_metric_cols]
    mean_df = grouped.mean().reset_index()
    std_df = grouped.std().reset_index()

    for metric in existing_metric_cols:
        mean_df[f"{metric}_std"] = std_df[metric]

    return mean_df


def add_warning(warnings: list[str], message: str) -> None:
    if message not in warnings:
        warnings.append(message)


# -----------------------------
# Report sections
# -----------------------------

def section_dataset_statistics(root: Path, warnings: list[str], max_rows: int) -> str:
    df, path = read_first_available([
        root / "results/tables/dataset_stats.csv",
        root / "results/tables/table1_dataset_stats.csv",
        root / "logs/split_audit.csv",
    ])

    if df is None:
        add_warning(warnings, "Missing dataset statistics: results/tables/dataset_stats.csv")
        return "## 1. Dataset statistics\n\n_Missing dataset statistics._\n\n"

    return (
        "## 1. Dataset statistics\n\n"
        f"Source file: `{relpath(path, root)}`\n\n"
        + dataframe_to_markdown(df, max_rows=max_rows)
        + "\n"
    )


def section_split_summary(root: Path, warnings: list[str], max_rows: int) -> str:
    df, path = read_first_available([
        root / "results/tables/split_report.csv",
        root / "results/tables/split_summary.csv",
        root / "logs/split_audit.csv",
    ])

    if df is None:
        add_warning(warnings, "Missing split summary: results/tables/split_report.csv")
        return "## 2. Split summary\n\n_Missing split summary._\n\n"

    # Warn if overlap columns show problems.
    for col in df.columns:
        if "overlap" in col.lower():
            try:
                if pd.to_numeric(df[col], errors="coerce").fillna(0).max() > 0:
                    add_warning(warnings, f"Potential split leakage: `{col}` contains non-zero values.")
            except Exception:
                pass

    return (
        "## 2. Split summary\n\n"
        f"Source file: `{relpath(path, root)}`\n\n"
        + dataframe_to_markdown(df, max_rows=max_rows)
        + "\n"
    )


def section_baseline_overall(root: Path, warnings: list[str], max_rows: int) -> str:
    summary_df, summary_path = read_first_available([
        root / "results/tables/overall_results_summary.csv",
        root / "results/tables/table3_overall_results.csv",
    ])

    if summary_df is not None:
        return (
            "## 3. Baseline overall results\n\n"
            f"Source file: `{relpath(summary_path, root)}`\n\n"
            + dataframe_to_markdown(summary_df, max_rows=max_rows)
            + "\n"
        )

    raw_df, raw_path = read_first_available([
        root / "results/tables/overall_results.csv",
        root / "results/tables/baseline_results.csv",
    ])

    if raw_df is None:
        add_warning(warnings, "Missing baseline overall results: results/tables/overall_results.csv")
        return "## 3. Baseline overall results\n\n_Missing baseline overall results._\n\n"

    group_cols = ["dataset", "split_mode", "split", "model", "baseline"]
    metric_cols = ["auc", "acc", "accuracy", "nll", "bce", "rmse"]

    summarized = summarize_numeric_by_group(raw_df, group_cols, metric_cols)

    return (
        "## 3. Baseline overall results\n\n"
        f"Source file: `{relpath(raw_path, root)}`\n\n"
        + dataframe_to_markdown(summarized, max_rows=max_rows)
        + "\n"
    )


def section_kc_bucket_distribution(root: Path, warnings: list[str], max_rows: int) -> str:
    df, path = read_first_available([
        root / "results/tables/bucket_distribution.csv",
        root / "results/tables/kc_bucket_distribution.csv",
    ])

    if df is not None:
        return (
            "## 4. KC bucket distribution\n\n"
            f"Source file: `{relpath(path, root)}`\n\n"
            + dataframe_to_markdown(df, max_rows=max_rows)
            + "\n"
        )

    strata_df, strata_path = read_first_available([
        root / "results/tables/kc_strata.csv",
    ])

    if strata_df is None:
        add_warning(warnings, "Missing KC bucket distribution: results/tables/bucket_distribution.csv or kc_strata.csv")
        return "## 4. KC bucket distribution\n\n_Missing KC bucket distribution._\n\n"

    if "bucket" not in strata_df.columns:
        add_warning(warnings, "KC strata file exists but has no `bucket` column.")
        return (
            "## 4. KC bucket distribution\n\n"
            f"Source file: `{relpath(strata_path, root)}`\n\n"
            "_Cannot infer distribution because `bucket` column is missing._\n\n"
        )

    group_cols = [c for c in ["dataset", "fold", "split_mode", "bucket"] if c in strata_df.columns]
    if not group_cols:
        group_cols = ["bucket"]

    dist = strata_df.groupby(group_cols, dropna=False).size().reset_index(name="n_kcs")

    return (
        "## 4. KC bucket distribution\n\n"
        f"Source file: `{relpath(strata_path, root)}`\n\n"
        + dataframe_to_markdown(dist, max_rows=max_rows)
        + "\n"
    )


def section_sparse_performance(root: Path, warnings: list[str], max_rows: int) -> str:
    summary_df, summary_path = read_first_available([
        root / "results/tables/metric_per_bucket_summary.csv",
        root / "results/tables/table4_metric_per_bucket.csv",
    ])

    if summary_df is not None:
        return (
            "## 5. Sparse-concept performance metrics\n\n"
            f"Source file: `{relpath(summary_path, root)}`\n\n"
            + dataframe_to_markdown(summary_df, max_rows=max_rows)
            + "\n"
        )

    raw_df, raw_path = read_first_available([
        root / "results/tables/metric_per_bucket.csv",
    ])

    if raw_df is None:
        add_warning(warnings, "Missing sparse-concept performance metrics: results/tables/metric_per_bucket.csv")
        return "## 5. Sparse-concept performance metrics\n\n_Missing sparse-concept performance metrics._\n\n"

    group_cols = ["dataset", "split_mode", "split", "model", "baseline", "bucket"]
    metric_cols = ["auc", "acc", "accuracy", "nll", "bce", "rmse", "n_test_events", "n_kcs"]

    summarized = summarize_numeric_by_group(raw_df, group_cols, metric_cols)

    return (
        "## 5. Sparse-concept performance metrics\n\n"
        f"Source file: `{relpath(raw_path, root)}`\n\n"
        + dataframe_to_markdown(summarized, max_rows=max_rows)
        + "\n"
    )


def section_calibration(root: Path, warnings: list[str], max_rows: int) -> str:
    parts = ["## 6. Calibration diagnostics\n\n"]

    ece_df, ece_path = read_first_available([
        root / "results/tables/ece_per_bucket.csv",
        root / "results/tables/calibration_results.csv",
    ])

    brier_df, brier_path = read_first_available([
        root / "results/tables/brier_decomposition_summary.csv",
        root / "results/tables/brier_decomposition.csv",
    ])

    if ece_df is None and brier_df is None:
        add_warning(warnings, "Missing calibration diagnostics: ECE and Brier files not found.")
        return "## 6. Calibration diagnostics\n\n_Missing calibration diagnostics._\n\n"

    if ece_df is not None:
        parts.append(f"### 6.1. ECE by KC bucket\n\nSource file: `{relpath(ece_path, root)}`\n\n")
        parts.append(dataframe_to_markdown(ece_df, max_rows=max_rows))
        parts.append("\n")
    else:
        add_warning(warnings, "Missing ECE file: results/tables/ece_per_bucket.csv")

    if brier_df is not None:
        parts.append(f"### 6.2. Brier decomposition\n\nSource file: `{relpath(brier_path, root)}`\n\n")

        # If raw seed-level file, summarize if possible.
        group_cols = ["dataset", "split_mode", "split", "model", "baseline", "bucket"]
        metric_cols = ["brier", "uncertainty", "reliability", "resolution"]

        if any(c in brier_df.columns for c in metric_cols):
            brier_show = summarize_numeric_by_group(brier_df, group_cols, metric_cols)
        else:
            brier_show = brier_df

        parts.append(dataframe_to_markdown(brier_show, max_rows=max_rows))
        parts.append("\n")
    else:
        add_warning(warnings, "Missing Brier decomposition file: results/tables/brier_decomposition.csv")

    return "".join(parts)


def section_reliability_links(root: Path, warnings: list[str]) -> str:
    fig_root = root / "results/figures"

    if not fig_root.exists():
        add_warning(warnings, "Missing figures directory: results/figures/")
        return "## 7. Reliability diagram links\n\n_Missing figures directory._\n\n"

    suffixes = {".png", ".jpg", ".jpeg", ".pdf", ".svg"}
    reliability_files = [
        p for p in fig_root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in suffixes
        and "reliability" in p.name.lower()
    ]

    if not reliability_files:
        add_warning(warnings, "No reliability diagram files found under results/figures/.")
        return "## 7. Reliability diagram links\n\n_No reliability diagrams found._\n\n"

    lines = ["## 7. Reliability diagram links\n\n"]
    for p in sorted(reliability_files):
        rp = relpath(p, root)
        lines.append(f"- [`{rp}`]({rp})\n")

    lines.append("\n")
    return "".join(lines)


def section_cold_start(root: Path, warnings: list[str], max_rows: int) -> str:
    df, path = read_first_available([
        root / "results/tables/cold_start_results.csv",
        root / "results/tables/table6_cold_start_results.csv",
    ])

    if df is None:
        add_warning(warnings, "Missing cold-start diagnostics: results/tables/cold_start_results.csv")
        return "## 8. Cold-start diagnostics\n\n_Missing cold-start diagnostics._\n\n"

    return (
        "## 8. Cold-start diagnostics\n\n"
        f"Source file: `{relpath(path, root)}`\n\n"
        + dataframe_to_markdown(df, max_rows=max_rows)
        + "\n"
    )


def section_sensitivity(root: Path, warnings: list[str], max_rows: int) -> str:
    df, path = read_first_available([
        root / "results/tables/sensitivity_analysis.csv",
        root / "results/tables/tableA1_sensitivity.csv",
    ])

    if df is None:
        add_warning(warnings, "Missing sensitivity analysis: results/tables/sensitivity_analysis.csv")
        return "## 9. Sensitivity analysis\n\n_Missing sensitivity analysis._\n\n"

    return (
        "## 9. Sensitivity analysis\n\n"
        f"Source file: `{relpath(path, root)}`\n\n"
        + dataframe_to_markdown(df, max_rows=max_rows)
        + "\n"
    )


def section_leakage_audit(root: Path, warnings: list[str], max_rows: int) -> str:
    df, path = read_first_available([
        root / "results/tables/leakage_audit_log.csv",
        root / "logs/leakage_audit_log.csv",
    ])

    if df is None:
        add_warning(warnings, "Missing leakage audit: results/tables/leakage_audit_log.csv")
        return "## 10. Leakage audit L1-L7\n\n_Missing leakage audit._\n\n"

    status_cols = [c for c in df.columns if c.lower() in {"status", "result", "pass_fail"}]
    for status_col in status_cols:
        statuses = df[status_col].astype(str).str.upper()
        if (statuses == "FAIL").any():
            add_warning(warnings, f"Leakage audit contains FAIL in column `{status_col}`.")
        if (statuses == "CAUTION").any():
            add_warning(warnings, f"Leakage audit contains CAUTION in column `{status_col}`.")

    text = (
        "## 10. Leakage audit L1-L7\n\n"
        f"Source file: `{relpath(path, root)}`\n\n"
        + dataframe_to_markdown(df, max_rows=max_rows)
        + "\n"
    )

    if status_cols:
        status_col = status_cols[0]
        summary = df[status_col].astype(str).str.upper().value_counts().reset_index()
        summary.columns = ["status", "count"]
        text += "### Leakage status summary\n\n"
        text += dataframe_to_markdown(summary, max_rows=max_rows)
        text += "\n"

    return text


def section_missing_outputs(root: Path, warnings: list[str]) -> str:
    required_files = [
        "results/tables/dataset_stats.csv",
        "results/tables/split_report.csv",
        "results/tables/overall_results.csv",
        "results/tables/kc_strata.csv",
        "results/tables/bucket_distribution.csv",
        "results/tables/metric_per_bucket.csv",
        "results/tables/ece_per_bucket.csv",
        "results/tables/brier_decomposition.csv",
        "results/tables/cold_start_results.csv",
        "results/tables/sensitivity_analysis.csv",
        "results/tables/leakage_audit_log.csv",
    ]

    missing = [f for f in required_files if not (root / f).exists()]

    lines = ["## 11. Missing outputs or warnings\n\n"]

    if not missing and not warnings:
        lines.append("No missing required outputs or warnings detected.\n\n")
        return "".join(lines)

    if missing:
        lines.append("### 11.1. Missing expected files\n\n")
        for f in missing:
            lines.append(f"- `{f}`\n")
        lines.append("\n")

    if warnings:
        lines.append("### 11.2. Warnings\n\n")
        for w in warnings:
            lines.append(f"- {w}\n")
        lines.append("\n")

    return "".join(lines)


# -----------------------------
# Paper Artifacts Generation
# -----------------------------

def generate_paper_artifacts(root: Path):
    print("Generating paper artifacts (LaTeX tables and figures)...")
    
    # Table 1: Stats
    df, _ = read_first_available([root / "logs/split_audit.csv"])
    if df is not None:
        stats = df.groupby('dataset').agg({'n_train': 'first', 'n_test': 'first'}).reset_index()
        df_to_latex(stats, root / "paper/tables/table1_dataset_stats.tex", "Dataset Statistics", "tab:datasets")
    
    # Table 2: Leakage
    df, _ = read_first_available([root / "results/tables/leakage_audit_log.csv"])
    if df is not None:
        df_to_latex(df, root / "paper/tables/table2_leakage_audit.tex", "Leakage Audit", "tab:leakage")
        
    # Table 3: Overall
    df, _ = read_first_available([root / "results/tables/overall_results_summary.csv"])
    if df is not None:
        cols = ['dataset', 'split_mode', 'model', 'auc_mean', 'acc_mean', 'nll_mean', 'rmse_mean']
        available_cols = [c for c in cols if c in df.columns]
        df_to_latex(df[available_cols], root / "paper/tables/table3_overall_results.tex", "Overall Performance", "tab:overall")
        
    # Table 4: Bucket
    df, _ = read_first_available([root / "results/tables/metric_per_bucket_summary.csv"])
    if df is not None:
        cols = ['dataset', 'model', 'bucket', 'auc_mean', 'acc_mean', 'nll_mean', 'rmse_mean']
        available_cols = [c for c in cols if c in df.columns]
        df_to_latex(df[available_cols], root / "paper/tables/table4_metric_per_bucket.tex", "Performance by Bucket", "tab:bucket")
        
    # Table 5: Calibration
    df, _ = read_first_available([root / "results/tables/ece_per_bucket.csv"])
    if df is not None:
        df['ece'] = pd.to_numeric(df['ece'], errors='coerce')
        summary = df.groupby(['dataset', 'model', 'bucket'])['ece'].mean().reset_index()
        df_to_latex(summary, root / "paper/tables/table5_calibration_per_bucket.tex", "Calibration by Bucket", "tab:calib")

    # Table 6: Cold-start
    df, _ = read_first_available([root / "results/tables/cold_start_results.csv"])
    if df is not None:
        df['auc'] = pd.to_numeric(df['auc'], errors='coerce')
        df['ece'] = pd.to_numeric(df['ece'], errors='coerce')
        summary = df.groupby(['dataset', 'model', 'group'])[['auc', 'ece']].mean().reset_index()
        df_to_latex(summary, root / "paper/tables/table6_cold_start_results.tex", "Cold-start Results", "tab:coldstart")

    # Table A1: Sensitivity
    df, _ = read_first_available([root / "results/tables/sensitivity_analysis.csv"])
    if df is not None:
        df['auc'] = pd.to_numeric(df['auc'], errors='coerce')
        df['ece'] = pd.to_numeric(df['ece'], errors='coerce')
        summary = df.groupby(['setting', 'bucket'])[['auc', 'ece']].mean().reset_index()
        df_to_latex(summary, root / "paper/tables/tableA1_sensitivity.tex", "Sensitivity Analysis", "tab:sens")

    # Figures
    ensure_parent_dir(root / "paper/figures/dummy.pdf")
    src_fig = root / "results/figures/kc_bucket_distribution.pdf"
    if src_fig.exists():
        shutil.copy(src_fig, root / "paper/figures/figure2_bucket_distribution.pdf")


# -----------------------------
# Main report generation
# -----------------------------

def generate_report(root: Path, output: Path, max_rows: int = 25) -> None:
    warnings: list[str] = []

    sections = []

    sections.append(
        "# P0 Diagnostic Report\n\n"
        "**Paper title:** Reproducible Sparse-Concept and Calibration Diagnostics for Knowledge Tracing\n\n"
        "**Report type:** protocol / diagnostic / resource report\n\n"
        f"**Generated at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "This report summarizes sparse-concept diagnostics, calibration diagnostics, "
        "cold-start concept analysis, and leakage auditing for Knowledge Tracing baselines. "
        "It does not report results for any new KT model, SSL module, GNN module, "
        "path recommendation method, or distillation method.\n\n"
    )

    sections.append(section_dataset_statistics(root, warnings, max_rows))
    sections.append(section_split_summary(root, warnings, max_rows))
    sections.append(section_baseline_overall(root, warnings, max_rows))
    sections.append(section_kc_bucket_distribution(root, warnings, max_rows))
    sections.append(section_sparse_performance(root, warnings, max_rows))
    sections.append(section_calibration(root, warnings, max_rows))
    sections.append(section_reliability_links(root, warnings))
    sections.append(section_cold_start(root, warnings, max_rows))
    sections.append(section_sensitivity(root, warnings, max_rows))
    sections.append(section_leakage_audit(root, warnings, max_rows))
    sections.append(section_missing_outputs(root, warnings))

    report_text = "\n".join(sections)

    ensure_parent_dir(output)
    output.write_text(report_text, encoding="utf-8")

    print(f"[OK] Generated report: {output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate P0 diagnostic Markdown report."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Project root directory. Default: current directory.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/reports/p0_diagnostic_report.md",
        help="Output Markdown report path.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=25,
        help="Maximum rows to show per table in the Markdown report.",
    )
    return parser.parse_args()


def main() -> None:
    import traceback
    try:
        args = parse_args()
        root = Path(args.project_root).resolve()
        output = (root / args.output).resolve()

        # 1. Generate Markdown report
        generate_report(root=root, output=output, max_rows=args.max_rows)
        
        # 2. Generate LaTeX paper artifacts
        generate_paper_artifacts(root=root)
    except Exception as e:
        traceback.print_exc()
        raise e


if __name__ == "__main__":
    main()
