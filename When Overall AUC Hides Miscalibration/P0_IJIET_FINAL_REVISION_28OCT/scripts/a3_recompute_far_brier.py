#!/usr/bin/env python3
"""A3: FAR and the Brier decomposition from primary-protocol prediction exports.

Models: ASSISTments DKT and T-KT masked, best validation AUC, windows of 200.
Rows: no_history == 0. Groups: sparse (20 <= f < 100) and dense (f >= 500),
read from the group column of each export. Threshold tau = 0.7.

FAR = P(y = 0 | p >= tau); FPR = P(p >= tau | y = 0);
E[FAR] = mean(1 - p | p >= tau); excess = FAR - E[FAR];
DeltaFAR = FAR_sparse - FAR_dense.

Fold 0 interval: KC-clustered percentile bootstrap, B = 2000, KCs resampled
with replacement within the sparse and the dense group of the same replicate.
A fresh numpy Generator seeded with 20261021 is used for each model.
A replicate whose advance set is empty in either group is counted and left out.

The Brier decomposition uses 15 equal-width bins (src/brier_decomposition.py).
Four-partition summaries average fold 2 and fold 3 first and use ddof = 1.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

INNER = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(INNER))

from src.brier_decomposition import compute_brier_decomposition  # noqa: E402

PRED = INNER / "results" / "predictions"
OUT = INNER / "P0_IJIET_FINAL_REVISION_28OCT" / "results"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
MODELS = (("dkt", "DKT"), ("tktc", "T-KT masked"))
TAU = 0.7
SEED = 20261021
B = 2000
GROUPS = ("sparse", "dense")


def load(model: str, fold: int, seed: int) -> pd.DataFrame:
    path = PRED / f"pred_assist2012_{model}_best_validxchunk_fold{fold}_{seed}.csv.gz"
    if not path.is_file():
        raise SystemExit(f"MISSING {path}")
    frame = pd.read_csv(path, usecols=["y", "p", "group", "no_history", "kc_id"])
    frame = frame[(frame["no_history"] == 0) & frame["group"].isin(GROUPS)]
    return frame[~frame["p"].isna()]


def far_stats(part: pd.DataFrame) -> dict:
    y = part["y"].to_numpy()
    p = part["p"].to_numpy(dtype=float)
    adv = p >= TAU
    inc = y == 0
    n_adv = int(adv.sum())
    n_inc = int(inc.sum())
    return {
        "N": int(len(y)),
        "N_adv": n_adv,
        "N_inc": n_inc,
        "FAR": float(np.mean(inc[adv])) if n_adv else float("nan"),
        "E_FAR": float(np.mean(1.0 - p[adv])) if n_adv else float("nan"),
        "FPR": float(np.mean(adv[inc])) if n_inc else float("nan"),
    }


def kc_table(part: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    adv = part["p"].to_numpy(dtype=float) >= TAU
    bad = adv & (part["y"].to_numpy() == 0)
    agg = (
        pd.DataFrame({"kc": part["kc_id"].to_numpy(), "adv": adv.astype(int), "bad": bad.astype(int)})
        .groupby("kc", sort=True)
        .sum()
    )
    return agg["adv"].to_numpy(), agg["bad"].to_numpy()


def bootstrap(sparse: pd.DataFrame, dense: pd.DataFrame, rng: np.random.Generator) -> dict:
    s_adv, s_bad = kc_table(sparse)
    d_adv, d_bad = kc_table(dense)
    far_s, far_d, delta = [], [], []
    invalid = 0
    for _ in range(B):
        i = rng.integers(0, len(s_adv), size=len(s_adv))
        j = rng.integers(0, len(d_adv), size=len(d_adv))
        na_s, na_d = s_adv[i].sum(), d_adv[j].sum()
        if na_s == 0 or na_d == 0:
            invalid += 1
            continue
        fs = s_bad[i].sum() / na_s
        fd = d_bad[j].sum() / na_d
        far_s.append(fs)
        far_d.append(fd)
        delta.append(fs - fd)

    def ci(values):
        lo, hi = np.percentile(values, [2.5, 97.5])
        return float(lo), float(hi)

    return {
        "sparse": ci(far_s),
        "dense": ci(far_d),
        "delta": ci(delta),
        "invalid": invalid,
        "n_kc_sparse": int(len(s_adv)),
        "n_kc_dense": int(len(d_adv)),
    }


def four(values: dict[int, float]) -> np.ndarray:
    return np.array(
        [values[0], values[1], 0.5 * (values[2] + values[3]), values[4]],
        dtype=float,
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    fold0_rows, part_rows, brier_rows = [], [], []
    for model, label in MODELS:
        for fold, seed in PAIRS:
            frame = load(model, fold, seed)
            print(f"LOADED {model} fold{fold} rows={len(frame)}", flush=True)
            stats = {g: far_stats(frame[frame["group"] == g]) for g in GROUPS}
            part_rows.append(
                {
                    "model": label,
                    "fold": fold,
                    "init_seed": seed,
                    **{f"{k}_{g}": v for g in GROUPS for k, v in stats[g].items()},
                    "DeltaFAR": stats["sparse"]["FAR"] - stats["dense"]["FAR"],
                }
            )
            for g in GROUPS:
                part = frame[frame["group"] == g]
                brier, unc, rel, res = compute_brier_decomposition(
                    part["y"].to_numpy().astype(float), part["p"].to_numpy(dtype=float), n_bins=15
                )
                brier_rows.append(
                    {"model": label, "fold": fold, "group": g, "N": len(part),
                     "Brier": brier, "UNC": unc, "REL": rel, "RES": res}
                )
            if fold == 0:
                rng = np.random.default_rng(SEED)
                boot = bootstrap(frame[frame["group"] == "sparse"], frame[frame["group"] == "dense"], rng)
                for g in GROUPS:
                    s = stats[g]
                    fold0_rows.append(
                        {
                            "model": label, "group": g, **s,
                            "FAR_ci_low": boot[g][0], "FAR_ci_high": boot[g][1],
                            "excess": s["FAR"] - s["E_FAR"],
                            "n_kcs": boot[f"n_kc_{g}"],
                            "DeltaFAR": stats["sparse"]["FAR"] - stats["dense"]["FAR"],
                            "DeltaFAR_ci_low": boot["delta"][0],
                            "DeltaFAR_ci_high": boot["delta"][1],
                            "bootstrap_B": B,
                            "bootstrap_invalid": boot["invalid"],
                            "seed": SEED,
                            "tau": TAU,
                        }
                    )
    fold0 = pd.DataFrame(fold0_rows)
    parts = pd.DataFrame(part_rows)
    brier = pd.DataFrame(brier_rows)
    fold0.to_csv(OUT / "A3_far_fold0.csv", index=False)
    parts.to_csv(OUT / "A3_far_partitions.csv", index=False)
    brier.to_csv(OUT / "A3_brier_partitions.csv", index=False)

    summary = []
    for _, label in MODELS:
        sub = parts[parts["model"] == label].set_index("fold")
        units = four(sub["DeltaFAR"].to_dict())
        summary.append(
            {
                "model": label,
                "mean_DeltaFAR": float(units.mean()),
                "sd_DeltaFAR": float(units.std(ddof=1)),
                "min_DeltaFAR": float(units.min()),
                "max_DeltaFAR": float(units.max()),
                "units_positive": int((units > 0).sum()),
                "mean_N_sparse": float(four(sub["N_sparse"].to_dict()).mean()),
                "mean_Nadv_sparse": float(four(sub["N_adv_sparse"].to_dict()).mean()),
                "mean_Ninc_sparse": float(four(sub["N_inc_sparse"].to_dict()).mean()),
                "mean_FAR_sparse": float(four(sub["FAR_sparse"].to_dict()).mean()),
                "mean_FAR_dense": float(four(sub["FAR_dense"].to_dict()).mean()),
            }
        )
    pd.DataFrame(summary).to_csv(OUT / "A3_far_four_partition.csv", index=False)

    bsum = []
    for _, label in MODELS:
        for g in GROUPS:
            sub = brier[(brier["model"] == label) & (brier["group"] == g)].set_index("fold")
            row = {"model": label, "group": g, "mean_N": float(four(sub["N"].to_dict()).mean())}
            for col in ("Brier", "UNC", "REL", "RES"):
                units = four(sub[col].to_dict())
                row[f"{col}_mean"] = float(units.mean())
                row[f"{col}_sd"] = float(units.std(ddof=1))
            bsum.append(row)
    pd.DataFrame(bsum).to_csv(OUT / "A3_brier_four_partition.csv", index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(fold0.round(4).to_string(index=False))
    print(pd.DataFrame(summary).round(4).to_string(index=False))
    print(pd.DataFrame(bsum).round(4).to_string(index=False))
    print("A3_RECOMPUTE = DONE", flush=True)


if __name__ == "__main__":
    main()
