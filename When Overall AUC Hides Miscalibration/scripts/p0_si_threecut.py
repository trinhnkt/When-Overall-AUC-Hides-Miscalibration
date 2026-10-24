#!/usr/bin/env python3
"""SI Table S7: three train-only frequency cut grids on frozen T-KT and DKT.

Does not overwrite Table 5 T-KT ECE 0.1136/0.2280. Main grid reprints
locked four-partition cells. Alt grids use the same 15-bin ECE on the
frozen rerun CSVs. Official SimpleKT is not regrouped (no pred CSVs).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "manuscript-pack"
if not REV.is_dir():
    REV = ROOT / "IJIET_FINAL_REVISION"
if not REV.is_dir():
    REV = ROOT
sys.path.insert(0, str(ROOT))
from src.calibration_eval import compute_ece  # noqa: E402

SEEDS = (42, 2024, 2025, 2026, 2027)
GRIDS = {
    "Main (20/100/500)": (20, 100, 500),
    "Alt-1 (10/50/250)": (10, 50, 250),
    "Alt-2 (30/150/750)": (30, 150, 750),
}
MODELS = (
    ("T-KT", "simplekt"),
    ("DKT", "dkt"),
)
LOCKED = {
    "T-KT": {"dense": (0.1136, 523971), "sparse": (0.2280, 415)},
    "DKT": {"dense": (0.0602, 523971), "sparse": (0.2333, 415)},
}


def pred_path(csv_model: str, seed: int) -> Path:
    rerun = (
        ROOT
        / "results/predictions"
        / f"assist2012_learner_based_{csv_model}_seed{seed}_predictions_rerun.csv"
    )
    if rerun.exists():
        return rerun
    return (
        ROOT
        / "results/predictions"
        / f"assist2012_learner_based_{csv_model}_seed{seed}.csv"
    )


def train_freq(fold: int) -> pd.Series:
    train = pd.read_csv(
        ROOT / f"data/processed/assist2012/splits/learner_based/fold_{fold}/train.csv",
        usecols=["kc_id"],
    )
    return train["kc_id"].value_counts()


def bucket(freq: float, t0: int, t1: int, t2: int) -> str:
    if freq == 0:
        return "cold"
    if freq < t0:
        return "very_sparse"
    if freq < t1:
        return "sparse"
    if freq < t2:
        return "medium"
    return "dense"


def four_part(vals: list[float]) -> float:
    return float(np.mean([vals[0], vals[1], 0.5 * (vals[2] + vals[3]), vals[4]]))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    freq_by_fold = {i: train_freq(i) for i in range(5)}
    rows = []
    for display, csv_model in MODELS:
        for gname, (t0, t1, t2) in GRIDS.items():
            ece_d, ece_s, n_d, n_s = [], [], [], []
            for seed in SEEDS:
                fold = SEEDS.index(seed)
                path = pred_path(csv_model, seed)
                if not path.exists():
                    raise SystemExit(f"missing {path}")
                pred = pd.read_csv(path, usecols=["kc_id", "y_true", "p_pred"])
                fmap = freq_by_fold[fold]
                pred["freq"] = pred["kc_id"].map(fmap).fillna(0)
                pred["bucket"] = [bucket(f, t0, t1, t2) for f in pred["freq"]]
                for bname, store_e, store_n in (
                    ("dense", ece_d, n_d),
                    ("sparse", ece_s, n_s),
                ):
                    sl = pred[pred["bucket"] == bname]
                    ece, *_ = compute_ece(
                        sl["y_true"].to_numpy(), sl["p_pred"].to_numpy(), n_bins=15
                    )
                    store_e.append(float(ece))
                    store_n.append(int(len(sl)))
            rec = {
                "model": display,
                "grid": gname,
                "t0": t0,
                "dense_ece": four_part(ece_d),
                "dense_n": four_part(n_d),
                "sparse_ece": four_part(ece_s),
                "sparse_n": four_part(n_s),
                "delta": four_part(ece_s) - four_part(ece_d),
            }
            rows.append(rec)
            print(display, gname, rec, flush=True)

    for r in rows:
        if r["delta"] <= 0:
            raise SystemExit(f"ordering flipped: {r}")

    out_csv = REV / "analysis" / "si_threecut_tkt_dkt.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_csv, index=False)

    def cell(x: float, nd=4) -> str:
        return f"{x:.{nd}f}"

    tex_rows = []
    for r in rows:
        if r["grid"].startswith("Main"):
            de, dn = LOCKED[r["model"]]["dense"]
            se, sn = LOCKED[r["model"]]["sparse"]
            note = " (Table 5)"
        else:
            de, dn = r["dense_ece"], r["dense_n"]
            se, sn = r["sparse_ece"], r["sparse_n"]
            note = ""
        tex_rows.append(
            f"{r['model']} & {r['grid']}{note} & {cell(de)} & {int(round(dn)):,} & "
            f"{cell(se)} & {int(round(sn)):,} & {cell(se - de)} \\\\"
        )

    tex = r"""\begin{table}[htbp]
\caption{Three train-only KC-frequency cut grids on ASSISTments 2012 (T-KT and DKT). Four-partition means (seeds 2025/2026 averaged first). Dense: $f\ge t_2$. Sparse: $t_0\le f<t_1$. Main reprints Table~5 ECE (T-KT $0.1136$/$0.2280$; DKT $0.0602$/$0.2333$). Alt grids use the same 15-bin ECE on the frozen rerun CSVs. Official SimpleKT~\cite{liu2023simplekt} is not regrouped here. Not a new model.}
\label{tab:s7_threecut}
\centering
\small
\begin{tabular}{llrrrrr}
\toprule
Model & Cut grid ($t_0/t_1/t_2$) & Dense ECE & $N$ dense & Sparse ECE & $N$ sparse & $\Delta$ECE \\
\midrule
""" + "\n".join(tex_rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    # SI has no bib; drop \cite if supplementary has no bibliography
    tex = tex.replace(
        r"Official SimpleKT~\cite{liu2023simplekt} is not regrouped here. ",
        "Official SimpleKT is not regrouped here. ",
    )
    tex_path = REV / "supplementary" / "Table_S7_threecut.tex"
    tex_path.write_text(tex, encoding="utf-8")
    summary = ROOT / "results/reports/p0_si_threecut.json"
    summary.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote {tex_path}", flush=True)


if __name__ == "__main__":
    main()
