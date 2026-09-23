#!/usr/bin/env python3
"""Rebuild frozen Appendix table CSVs from summaries. Does not retrain.

Verifies locked ASSISTments T-KT ECE 0.1136 / 0.2280 in the four-partition
CSV. Does not overwrite those cells. XES rows use the masked a2b summary
(same N / ECE series as main-text Table 5).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "IJIET_FINAL_REVISION"
if not REV.is_dir():
    REV = ROOT
MAIN_CSV = REV / "analysis" / "summary_4part_bucket.csv"
XES_CSV = REV / "a2b" / "analysis" / "summary_4part_bucket.csv"
OFFICIAL = ROOT / "results" / "reports" / "p0_official_simplekt_assist_ece.json"
SUP = REV / "supplementary"
LOCK_DENSE = 0.1136
LOCK_SPARSE = 0.2280

DS_LABEL = {
    "assist2012": "ASSISTments 2012",
    "junyi": "Junyi Academy",
    "xes3g5m": "XES3G5M",
}
MODEL_LABEL = {
    "irt_1pl": "IRT",
    "dkt": "DKT",
    "simplekt": "T-KT",
}
STRATA = ("dense", "medium", "sparse")


def fmt(mean: float, sd: float | None = None) -> str:
    if pd.isna(mean):
        return "—"
    if sd is None or pd.isna(sd):
        return f"{mean:.4f}"
    return f"${mean:.4f}\\pm{sd:.4f}$"


def n_cell(n: float) -> str:
    return f"{int(round(n)):,}"


def load_parts() -> pd.DataFrame:
    main = pd.read_csv(MAIN_CSV)
    xes = pd.read_csv(XES_CSV)
    a = main[main["dataset"].isin(("assist2012", "junyi"))].copy()
    x = xes[xes["dataset"] == "xes3g5m"].copy()
    return pd.concat([a, x], ignore_index=True)


def verify_locks(df: pd.DataFrame) -> None:
    tkt = df[(df["dataset"] == "assist2012") & (df["model"] == "simplekt")]
    dense = float(tkt.loc[tkt["bucket"] == "dense", "ece_mean"].iloc[0])
    sparse = float(tkt.loc[tkt["bucket"] == "sparse", "ece_mean"].iloc[0])
    if round(dense, 4) != LOCK_DENSE:
        raise SystemExit(f"T-KT dense ECE {dense} != {LOCK_DENSE}")
    if round(sparse, 4) != LOCK_SPARSE:
        raise SystemExit(f"T-KT sparse ECE {sparse} != {LOCK_SPARSE}")


def write_s8(df: pd.DataFrame) -> None:
    rows: list[str] = []
    for ds in ("assist2012", "junyi", "xes3g5m"):
        block = []
        for model in ("irt_1pl", "dkt", "simplekt"):
            for bucket in STRATA:
                sl = df[
                    (df["dataset"] == ds)
                    & (df["model"] == model)
                    & (df["bucket"] == bucket)
                ]
                if sl.empty:
                    continue
                r = sl.iloc[0]
                if pd.isna(r["n_events_mean"]) or float(r["n_events_mean"]) < 1:
                    continue
                if ds == "junyi" and bucket == "sparse":
                    continue
                block.append(
                    f"{DS_LABEL[ds]} & {MODEL_LABEL[model]} & {bucket} & "
                    f"{n_cell(r['n_events_mean'])} & "
                    f"{fmt(r['auc_mean'], r['auc_std'])} & "
                    f"{fmt(r['acc_mean'], r['acc_std'])} \\\\"
                )
        rows.extend(block)
        if ds != "xes3g5m":
            rows.append("\\midrule")

    official_rows = []
    if OFFICIAL.exists():
        js = json.loads(OFFICIAL.read_text(encoding="utf-8"))
        for bucket in STRATA:
            st = js["strata"][bucket]
            official_rows.append(
                f"ASSISTments 2012 & SimpleKT [4] & {bucket} & "
                f"{n_cell(st['n'])} & ${st['auc']:.4f}$ & — \\\\"
            )
        rows.append("\\midrule")
        rows.extend(official_rows)

    tex = r"""\begin{table}[htbp]
\caption{Four-partition AUC and ACC by train-only frequency stratum (seeds 2025/2026 averaged first). Complements main-text Table~4 (overall AUC/ACC), Table~5 (ECE), and Table~6 (Brier). ASSISTments and Junyi: \texttt{analysis/summary\_4part\_bucket.csv}. XES3G5M: masked a2b summary (same $N$ as Table~5). T-KT is the local Transformer, not published SimpleKT. Official SimpleKT [4] ASSISTments AUC is the four-partition mean from \texttt{p0\_official\_simplekt\_assist\_ece.json} (ACC per stratum not exported). Junyi sparse is empty. Does not change locked T-KT ECE $0.1136$/$0.2280$.}
\label{tab:s8_bucket_disc}
\centering
\small
\resizebox{\textwidth}{!}{%
\begin{tabular}{lllrrr}
\toprule
Dataset & Model & Stratum & $N$ & AUC & ACC \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}%
}
\end{table}
"""
    path = SUP / "Table_S8_bucket_auc_acc.tex"
    path.write_text(tex, encoding="utf-8")
    print(f"wrote {path}", flush=True)


def write_s9() -> None:
    tex = r"""\begin{table}[htbp]
\caption{Baseline inventory against Survey Roadmap v3.0 $\S$1.2 / item 6. P0 is a diagnostic paper: baselines illustrate the protocol. BKT is not scored. IRT fills the classical slot after pyBKT 1.4.1 degenerated on ASSISTments seed 42 (roadmap fallback: two stable baselines plus a documented classical reference). Official SimpleKT [4] is the pyKT-family strong baseline on ASSISTments only; [4] does not report ASSISTments 2012, so this paper does not claim a $2$--$3\%$ match to a published pyKT cell on that log. T-KT is a local Transformer and is not [4].}
\label{tab:s9_baseline_inventory}
\centering
\small
\begin{tabular}{llll}
\toprule
Roadmap slot & Required level & Scored in this P0 & Note \\
\midrule
BKT & Minimum (classical) & No & pyBKT degenerate; IRT used instead \\
IRT & Fallback classical & Yes (3 logs) & Base-rate / Rasch reference \\
DKT & Minimum & Yes (3 logs) & Local sequence baseline \\
simpleKT or AKT & Minimum (strong) & Official SimpleKT on ASSISTments & Not a published 2012 pyKT cell \\
T-KT (local) & Diagnostic Transformer & Yes (3 logs) & Not published SimpleKT [4] \\
AKT / DKVMN / sparseKT & Good / Excellent & No & Out of P0 scope \\
\bottomrule
\end{tabular}
\end{table}
"""
    path = SUP / "Table_S9_baseline_inventory.tex"
    path.write_text(tex, encoding="utf-8")
    print(f"wrote {path}", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    df = load_parts()
    verify_locks(df)
    write_s8(df)
    write_s9()
    print("locks OK: T-KT ECE 0.1136 / 0.2280", flush=True)


if __name__ == "__main__":
    main()
