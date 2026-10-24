#!/usr/bin/env python3
"""Recompute learner-based Tables 3/5/9 on 4 unique partitions.

Seeds 2025 and 2026 share one student split (fold_2 == fold_3). This script:

1. Scores each official rerun prediction file with fold-specific f_train.
2. Aggregates five-run mean±sd (status quo) and four-partition mean±sd
   (average the two inits on the duplicated split, then mean±sd over 4 partitions).
3. Writes comparison CSVs and replacement TeX if requested.

Does not train. Does not retune Direction C.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.kc_strata import get_bucket  # noqa: E402

PRED = ROOT / "results" / "predictions"
DATA = ROOT / "data" / "processed"
OUT = ROOT / "analysis" / "four_partition"
TABLES = ROOT / "results" / "tables"

SPLIT = "learner_based"
SEEDS = (42, 2024, 2025, 2026, 2027)
DATASETS = ("assist2012", "junyi", "xes3g5m")
MODELS = ("irt_1pl", "dkt", "simplekt")
BUCKETS = ("dense", "medium", "sparse", "very_sparse", "strict_cold_start")
N_BINS = 15

# Duplicate split: seeds 2025 (fold_2) and 2026 (fold_3)
DUP_A, DUP_B = 2025, 2026


def kc_key(x) -> str:
    return str(x).replace(".0", "")


def flag(n: float) -> str:
    if n >= 1000:
        return "R"
    if n >= 100:
        return "L"
    return "I"


def pred_path(dataset: str, model: str, seed: int) -> Path | None:
    for name in (
        f"{dataset}_{SPLIT}_{model}_seed{seed}_predictions_rerun.csv",
        f"{dataset}_{SPLIT}_{model}_seed{seed}.csv",
    ):
        p = PRED / name
        if p.exists():
            return p
    return None


def train_freq_map(dataset: str, fold: int) -> dict[str, int]:
    train = pd.read_csv(
        DATA / dataset / "splits" / SPLIT / f"fold_{fold}" / "train.csv",
        usecols=["kc_id"],
    )
    vc = train["kc_id"].map(kc_key).value_counts()
    return {k: int(v) for k, v in vc.items()}


def compute_ece(y: np.ndarray, p: np.ndarray, n_bins: int = N_BINS) -> float:
    n = y.size
    if n == 0:
        return np.nan
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.digitize(p, edges[1:-1], right=True)
    ece = 0.0
    for m in range(n_bins):
        mask = idx == m
        n_m = int(mask.sum())
        if n_m == 0:
            continue
        ece += (n_m / n) * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return ece


def brier_decomp(y: np.ndarray, p: np.ndarray, n_bins: int = N_BINS):
    n = y.size
    if n == 0:
        return np.nan, np.nan, np.nan, np.nan
    y_bar = float(y.mean())
    unc = y_bar * (1.0 - y_bar)
    brier = float(np.mean((p - y) ** 2))
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.digitize(p, edges[1:-1], right=True)
    rel = 0.0
    res = 0.0
    for m in range(n_bins):
        mask = idx == m
        n_m = int(mask.sum())
        if n_m == 0:
            continue
        acc_m = float(y[mask].mean())
        conf_m = float(p[mask].mean())
        rel += n_m * (conf_m - acc_m) ** 2
        res += n_m * (acc_m - y_bar) ** 2
    return brier, unc, rel / n, res / n


def calculate_metrics(y: np.ndarray, p: np.ndarray):
    from sklearn.metrics import roc_auc_score

    if y.size == 0:
        return np.nan, np.nan, np.nan, np.nan
    p_c = np.clip(p, 1e-15, 1.0 - 1e-15)
    auc = roc_auc_score(y, p_c) if len(np.unique(y)) >= 2 else np.nan
    acc = float(np.mean(y == (p_c >= 0.5)))
    nll = float(-np.mean(y * np.log(p_c) + (1.0 - y) * np.log(1.0 - p_c)))
    rmse = float(np.sqrt(np.mean((p_c - y) ** 2)))
    return auc, acc, nll, rmse


def partition_id(seed: int) -> str:
    if seed in (DUP_A, DUP_B):
        return "P2_dup"
    return f"P_{seed}"


def agg_units(df: pd.DataFrame, keys: list[str], metric_cols: list[str]) -> pd.DataFrame:
    """Collapse duplicate-split inits, then mean±sd over 4 partitions."""
    work = df.copy()
    work["partition"] = work["seed"].map(partition_id)
    part = (
        work.groupby(keys + ["partition"], dropna=False)[metric_cols]
        .mean()
        .reset_index()
    )
    g = part.groupby(keys, dropna=False)
    out = g[metric_cols].mean().add_suffix("_mean")
    out = out.join(g[metric_cols].std(ddof=1).add_suffix("_std"))
    out = out.join(g.size().rename("n_partitions"))
    return out.reset_index()


def agg_five(df: pd.DataFrame, keys: list[str], metric_cols: list[str]) -> pd.DataFrame:
    g = df.groupby(keys, dropna=False)
    out = g[metric_cols].mean().add_suffix("_mean")
    out = out.join(g[metric_cols].std(ddof=1).add_suffix("_std"))
    out = out.join(g.size().rename("n_runs"))
    return out.reset_index()


def fmt(mean, std) -> str:
    if pd.isna(mean) or mean is None:
        return "-"
    if pd.isna(std) or std is None or float(std) == 0.0:
        return f"${mean:.4f}$"
    return f"${mean:.4f} \\pm {std:.4f}$"


def ds_display(name: str) -> str:
    return {
        "assist2012": "ASSISTments 2012",
        "junyi": "Junyi Academy",
        "xes3g5m": "XES3G5M",
    }[name]


def model_display(name: str) -> str:
    return {"irt_1pl": "IRT", "dkt": "DKT", "simplekt": "SimpleKT"}[name]


def bucket_display(name: str) -> str:
    return {
        "dense": "dense",
        "medium": "medium",
        "sparse": "sparse",
        "very_sparse": "Very Sparse",
        "strict_cold_start": "Strict Cold-start",
    }[name]


def score_all() -> tuple[pd.DataFrame, pd.DataFrame]:
    overall_rows = []
    bucket_rows = []
    freq_cache: dict[tuple[str, int], dict[str, int]] = {}

    for ds in DATASETS:
        for fold, seed in enumerate(SEEDS):
            key = (ds, fold)
            if key not in freq_cache:
                print(f"freq {ds} fold_{fold}", flush=True)
                freq_cache[key] = train_freq_map(ds, fold)
            freq = freq_cache[key]
            for model in MODELS:
                path = pred_path(ds, model, seed)
                if path is None:
                    print(f"  MISSING {ds}/{model}/seed{seed}", flush=True)
                    continue
                print(f"  score {path.name}", flush=True)
                df = pd.read_csv(path, usecols=["kc_id", "y_true", "p_pred"])
                df = df.dropna(subset=["y_true", "p_pred"])
                df = df[df["kc_id"].astype(str) != "-1"]
                df = df[df["kc_id"].astype(str).str.lower() != "nan"]
                if df.empty:
                    continue
                y = df["y_true"].to_numpy(dtype=int)
                p = df["p_pred"].to_numpy(dtype=float)
                auc, acc, nll, rmse = calculate_metrics(y, p)
                overall_rows.append(
                    {
                        "dataset": ds,
                        "model": model,
                        "seed": seed,
                        "fold": fold,
                        "n_events": int(y.size),
                        "auc": auc,
                        "acc": acc,
                        "nll": nll,
                        "rmse": rmse,
                    }
                )
                ftrain = df["kc_id"].map(lambda k: freq.get(kc_key(k), 0)).to_numpy()
                buckets = np.array([get_bucket(int(v)) for v in ftrain])
                kc = df["kc_id"].map(kc_key).to_numpy()
                for b in BUCKETS:
                    mask = buckets == b
                    if not mask.any():
                        continue
                    yb, pb = y[mask], p[mask]
                    bauc, bacc, bnll, brmse = calculate_metrics(yb, pb)
                    ece = compute_ece(yb, pb)
                    brier, unc, rel, res = brier_decomp(yb, pb)
                    bucket_rows.append(
                        {
                            "dataset": ds,
                            "model": model,
                            "seed": seed,
                            "fold": fold,
                            "bucket": b,
                            "n_kcs": int(pd.unique(kc[mask]).size),
                            "n_events": int(mask.sum()),
                            "auc": bauc,
                            "acc": bacc,
                            "nll": bnll,
                            "rmse": brmse,
                            "ece": ece,
                            "brier": brier,
                            "uncertainty": unc,
                            "reliability": rel,
                            "resolution": res,
                        }
                    )
    return pd.DataFrame(overall_rows), pd.DataFrame(bucket_rows)


def write_tex_table3(sum5: pd.DataFrame, sum4: pd.DataFrame) -> str:
    lines = [
        r"\begin{table}[tbp]",
        r"\caption{Overall Performance under Learner-based Split}",
        r"\label{tab:overall_learner}",
        r"\centering",
        r"\resizebox{\columnwidth}{!}{%",
        r"\begin{tabular}{lllcccc}",
        r"\toprule",
        r"Dataset & Split & Model & AUC & ACC & NLL & RMSE \\",
        r"\midrule",
    ]
    last_ds = None
    for ds in DATASETS:
        for model in MODELS:
            row = sum4[(sum4["dataset"] == ds) & (sum4["model"] == model)]
            if row.empty:
                continue
            r = row.iloc[0]
            ds_col = ds_display(ds) if ds != last_ds else ""
            last_ds = ds
            lines.append(
                f"{ds_col} & Learner-based & {model_display(model)} & "
                f"{fmt(r['auc_mean'], r['auc_std'])} & "
                f"{fmt(r['acc_mean'], r['acc_std'])} & "
                f"{fmt(r['nll_mean'], r['nll_std'])} & "
                f"{fmt(r['rmse_mean'], r['rmse_std'])} \\\\"
            )
        lines.append(r"\midrule")
    if lines[-1] == r"\midrule":
        lines[-1] = r"\bottomrule"
    lines += [
        r"",
        r"\end{tabular}%",
        r"}",
        r"",
        r"\vspace{1ex}",
        r"{\scriptsize \textbf{Note:} Mean $\pm$ standard deviation over four unique learner-based partitions. "
        r"Seeds 2025 and 2026 share one student split (\texttt{fold\_2}$=$\texttt{fold\_3}); their metrics are averaged "
        r"into one partition value before the four-partition summary. IRT is the classical baseline. Under learner-based "
        r"splits, IRT's AUC remains at 0.5000 because unseen learners do not have estimated ability parameters, causing "
        r"the model to fall back to a constant or base-rate-like prediction. Consequently, its ACC mainly reflects "
        r"majority-class base-rate and thresholding behavior rather than discriminative ranking ability.\par}",
        r"",
        r"\end{table}",
        r"",
    ]
    _ = sum5  # kept for comparison CSVs
    return "\n".join(lines)


def write_tex_table5(sum4: pd.DataFrame) -> str:
    lines = [
        r"\begin{table}[tbp]",
        r"\caption{Knowledge Tracing Performance Breakdown by KC-frequency Strata (Learner-based Split)}",
        r"\label{tab:strata_learner}",
        r"\centering",
        r"\resizebox{\columnwidth}{!}{%",
        r"\begin{tabular}{lllcrccccc}",
        r"\toprule",
        r"Dataset & Model & Bucket & Rel. & \#KCs & \#Events & AUC & ACC & NLL & RMSE \\",
        r"\midrule",
    ]
    last_ds = None
    last_model = None
    for ds in DATASETS:
        for model in MODELS:
            for b in BUCKETS:
                row = sum4[
                    (sum4["dataset"] == ds)
                    & (sum4["model"] == model)
                    & (sum4["bucket"] == b)
                ]
                if row.empty:
                    continue
                r = row.iloc[0]
                n_ev = int(round(float(r["n_events_mean"])))
                n_kc = int(round(float(r["n_kcs_mean"])))
                ds_col = ds_display(ds) if ds != last_ds else ""
                model_col = model_display(model) if model != last_model else ""
                last_ds, last_model = ds, model
                lines.append(
                    f"{ds_col} & {model_col} & {bucket_display(b)} & {flag(n_ev)} & "
                    f"{n_kc:,} & {n_ev:,} & "
                    f"{fmt(r['auc_mean'], r['auc_std'])} & "
                    f"{fmt(r['acc_mean'], r['acc_std'])} & "
                    f"{fmt(r['nll_mean'], r['nll_std'])} & "
                    f"{fmt(r['rmse_mean'], r['rmse_std'])} \\\\"
                )
        lines.append(r"\midrule")
    if lines[-1] == r"\midrule":
        lines[-1] = r"\bottomrule"
    lines += [
        r"",
        r"\end{tabular}%",
        r"}",
        r"",
        r"\vspace{1ex}",
        r"{\scriptsize \textbf{Note:} Reliability flags are assigned by the number of evaluated test events: Reliable "
        r"(R: $N \ge 1000$), Limited (L: $100 \le N < 1000$), and Insufficient (I: $N < 100$). Results in Insufficient "
        r"buckets are descriptive only. Mean $\pm$ standard deviation and event counts are over four unique learner-based "
        r"partitions (seeds 2025 and 2026 averaged first). After test-fold filtering and KC-strata matching, the evaluated "
        r"learner-based KC totals are reported per row. Within a stratum, evaluated event counts may differ across models. "
        r"This bidirectional variance occurs because (1) sequence models often drop initial interactions lacking prior "
        r"state or apply minimum-length filtering, reducing dense-event totals compared to classical IRT; (2) IRT "
        r"implementations often fail to output predictions for concepts with insufficient training history, while deep "
        r"models still generate predictions via initialized embeddings, increasing their sparse-event totals; and "
        r"(3) codebase-specific windowing and padding choices cause further discrepancies.\par}",
        r"",
        r"\end{table}",
        r"",
    ]
    return "\n".join(lines)


def write_tex_table9(sum4: pd.DataFrame) -> str:
    lines = [
        r"\begin{table*}[htbp]",
        r"\caption{Calibration Breakdown by Frequency Stratum}",
        r"\label{tab:calibration_learner}",
        r"\centering",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lllrcccccc}",
        r"\toprule",
        r"Dataset & Model & Bucket & Rel. & \#Events & ECE & Brier & UNC & REL & RES \\",
        r"\midrule",
    ]
    last_ds = None
    last_model = None
    for ds in DATASETS:
        for model in MODELS:
            for b in BUCKETS:
                row = sum4[
                    (sum4["dataset"] == ds)
                    & (sum4["model"] == model)
                    & (sum4["bucket"] == b)
                ]
                if row.empty:
                    continue
                r = row.iloc[0]
                n_ev = int(round(float(r["n_events_mean"])))
                ds_col = ds_display(ds) if ds != last_ds else ""
                model_col = model_display(model) if model != last_model else ""
                last_ds, last_model = ds, model
                unc_std = r.get("uncertainty_std", 0.0)
                rel_std = r.get("reliability_std", 0.0)
                res_std = r.get("resolution_std", 0.0)
                # Match published table: UNC/REL/RES as means without ± when tiny
                unc_str = f"${r['uncertainty_mean']:.4f}$"
                rel_str = f"${r['reliability_mean']:.4f}$"
                res_str = f"${r['resolution_mean']:.4f}$"
                _ = (unc_std, rel_std, res_std)
                lines.append(
                    f"{ds_col} & {model_col} & {bucket_display(b)} & {flag(n_ev)} & "
                    f"{n_ev:,} & {fmt(r['ece_mean'], r['ece_std'])} & "
                    f"{fmt(r['brier_mean'], r['brier_std'])} & "
                    f"{unc_str} & {rel_str} & {res_str} \\\\"
                )
        lines.append(r"\midrule")
    if lines[-1] == r"\midrule":
        lines[-1] = r"\bottomrule"
    lines += [
        r"",
        r"\end{tabular}%",
        r"}",
        r"",
        r"\vspace{1ex}",
        r"{\scriptsize \textbf{Note:} Reliability flags (R/L/I) follow Section 3.5. Mean $\pm$ standard deviation and "
        r"event counts are over four unique learner-based partitions (seeds 2025 and 2026 averaged first). IRT shows "
        r"low ECE in several learner-based cohorts, but $\text{RES} = 0$ across strata indicates base-rate-like "
        r"behavior with no resolving power (Section 4.2); IRT calibration should therefore be interpreted jointly "
        r"with AUC and Brier resolution.\par}",
        r"",
        r"\end{table*}",
        r"",
    ]
    return "\n".join(lines)


def compare_published(sum5_ov: pd.DataFrame, sum5_bk: pd.DataFrame) -> pd.DataFrame:
    """Compare 5-run fold-specific recompute against published table digits."""
    pub = pd.read_csv(TABLES / "metric_per_bucket_summary.csv")
    rows = []
    punch = [
        ("assist2012", "simplekt", "dense", "ece", 0.1131),
        ("assist2012", "simplekt", "medium", "ece", 0.1578),
        ("assist2012", "simplekt", "sparse", "ece", 0.2254),
        ("assist2012", "simplekt", "sparse", "auc", 0.7197),
        ("xes3g5m", "dkt", "sparse", "auc", 0.8547),
        ("xes3g5m", "simplekt", "sparse", "auc", 0.8455),
    ]
    for ds, model, bucket, metric, published in punch:
        hit = sum5_bk[
            (sum5_bk["dataset"] == ds)
            & (sum5_bk["model"] == model)
            & (sum5_bk["bucket"] == bucket)
        ]
        val = float(hit.iloc[0][f"{metric}_mean"]) if not hit.empty else np.nan
        rows.append(
            {
                "dataset": ds,
                "model": model,
                "bucket": bucket,
                "metric": metric,
                "published": published,
                "recompute_5run": val,
                "delta": val - published if pd.notna(val) else np.nan,
            }
        )
    ov_pub = [
        ("assist2012", "simplekt", "auc", 0.6840),
        ("assist2012", "dkt", "auc", 0.6980),
        ("xes3g5m", "dkt", "auc", 0.8170),
    ]
    for ds, model, metric, published in ov_pub:
        hit = sum5_ov[(sum5_ov["dataset"] == ds) & (sum5_ov["model"] == model)]
        val = float(hit.iloc[0][f"{metric}_mean"]) if not hit.empty else np.nan
        rows.append(
            {
                "dataset": ds,
                "model": model,
                "bucket": "overall",
                "metric": metric,
                "published": published,
                "recompute_5run": val,
                "delta": val - published if pd.notna(val) else np.nan,
            }
        )
    _ = pub
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    overall, bucket = score_all()
    overall.to_csv(OUT / "per_seed_overall.csv", index=False)
    bucket.to_csv(OUT / "per_seed_bucket.csv", index=False)

    ov_metrics = ["n_events", "auc", "acc", "nll", "rmse"]
    bk_metrics = [
        "n_kcs",
        "n_events",
        "auc",
        "acc",
        "nll",
        "rmse",
        "ece",
        "brier",
        "uncertainty",
        "reliability",
        "resolution",
    ]
    ov_keys = ["dataset", "model"]
    bk_keys = ["dataset", "model", "bucket"]

    sum5_ov = agg_five(overall, ov_keys, ov_metrics)
    sum4_ov = agg_units(overall, ov_keys, ov_metrics)
    sum5_bk = agg_five(bucket, bk_keys, bk_metrics)
    sum4_bk = agg_units(bucket, bk_keys, bk_metrics)

    sum5_ov.to_csv(OUT / "summary_5run_overall.csv", index=False)
    sum4_ov.to_csv(OUT / "summary_4part_overall.csv", index=False)
    sum5_bk.to_csv(OUT / "summary_5run_bucket.csv", index=False)
    sum4_bk.to_csv(OUT / "summary_4part_bucket.csv", index=False)

    cmp = compare_published(sum5_ov, sum5_bk)
    cmp.to_csv(OUT / "compare_published.csv", index=False)

    # Punchline 4-part vs 5-run
    punch_rows = []
    for label, sdf in (("5run", sum5_bk), ("4part", sum4_bk)):
        for bucket_name in ("dense", "medium", "sparse"):
            hit = sdf[
                (sdf["dataset"] == "assist2012")
                & (sdf["model"] == "simplekt")
                & (sdf["bucket"] == bucket_name)
            ].iloc[0]
            punch_rows.append(
                {
                    "agg": label,
                    "bucket": bucket_name,
                    "ece": hit["ece_mean"],
                    "ece_std": hit["ece_std"],
                    "n_events": hit["n_events_mean"],
                    "n_kcs": hit["n_kcs_mean"],
                }
            )
    pd.DataFrame(punch_rows).to_csv(OUT / "punchline_ece.csv", index=False)

    (OUT / "table_03_four_partition.tex").write_text(
        write_tex_table3(sum5_ov, sum4_ov), encoding="utf-8"
    )
    (OUT / "table_05_four_partition.tex").write_text(
        write_tex_table5(sum4_bk), encoding="utf-8"
    )
    (OUT / "table_09_four_partition.tex").write_text(
        write_tex_table9(sum4_bk), encoding="utf-8"
    )

    print("\n=== compare vs published ===", flush=True)
    print(cmp.to_string(index=False), flush=True)
    print("\n=== punchline ECE ===", flush=True)
    print(pd.DataFrame(punch_rows).to_string(index=False), flush=True)
    print(f"\nWrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
