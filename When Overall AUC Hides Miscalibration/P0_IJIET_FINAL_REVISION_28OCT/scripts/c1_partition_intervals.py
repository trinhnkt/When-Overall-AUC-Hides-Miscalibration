"""C1: learner-cluster bootstrap interval of the size-matched gap G for every unique partition.

Usage:
    py -3 c1_partition_intervals.py points {dkt|tktc}
    py -3 c1_partition_intervals.py boot {dkt|tktc} {1|23|4}
    py -3 c1_partition_intervals.py combine

points  replays the published stream (seed 20261021, folds 0-4 in order, fold-0 bootstrap included),
        so the per-partition G and the fold-0 interval equal the published values.
boot    draws the interval for one other partition with a separate Generator seeded [20261021, fold].
        For folds 2-3 the two runs share learners: each replicate resamples learner indices once,
        computes G on fold 2 and on fold 3 with the same picks, and stores their mean.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if (HERE / "reproduce_tables.py").is_file():
    import reproduce_tables as rt  # noqa: E402
    from published_gap import _concat_picked, size_matched_contrast  # noqa: E402

    OUT = HERE.parent / "statistics" / "partition_intervals"
    RESULT = OUT / "C1_PARTITION_INTERVALS.csv"
else:
    import a5_far_brier  # noqa: E402
    import a5_published_gap  # noqa: E402

    sys.modules.setdefault("far_brier", a5_far_brier)
    sys.modules.setdefault("published_gap", a5_published_gap)
    import a5_reproduce_tables as rt  # noqa: E402
    from a5_published_gap import _concat_picked, size_matched_contrast  # noqa: E402

    rt.PRED = HERE.parents[1] / "results" / "predictions"
    OUT = HERE.parent / "results" / "C1"
    RESULT = HERE.parent / "results" / "C1_PARTITION_INTERVALS.csv"
SEED = 20261021
PAIRS = dict(rt.PAIRS)


def frame(model: str, fold: int) -> pd.DataFrame:
    return rt.load(rt.pred_name("assist2012", model, "best_valid", "chunk", fold, PAIRS[fold]))


def points(model: str) -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    for fold in range(5):
        stats = rt.uncertainty(frame(model, fold), "sparse", rng, bootstrap=(fold == 0))
        stats["fold"] = fold
        rows.append(stats)
        print(f"{model} fold{fold} G={stats['gap']:.4f} N={stats['n_focal']}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / f"points_{model}.csv", index=False)


def user_lists(df: pd.DataFrame, users: list) -> tuple[list, list]:
    kept = df[df["no_history"] == 0]
    grouped = {uid: g for uid, g in kept.groupby("user_id", sort=False)}
    empty = (np.array([], dtype=int), np.array([], dtype=float))
    sparse, dense = [], []
    for uid in users:
        g = grouped.get(uid)
        if g is None:
            sparse.append(empty)
            dense.append(empty)
            continue
        s = g[g["group"] == "sparse"]
        d = g[g["group"] == "dense"]
        sparse.append((s["y"].to_numpy(), s["p"].to_numpy(dtype=float)))
        dense.append((d["y"].to_numpy(), d["p"].to_numpy(dtype=float)))
    return sparse, dense


def replicate_gap(user_s, user_d, pick, inner) -> float | None:
    sparse = _concat_picked(user_s, pick)
    if sparse is None:
        return None
    clusters = [user_d[int(j)] for j in pick if len(user_d[int(j)][0])]
    if not clusters:
        return None
    row = size_matched_contrast(sparse[0], sparse[1], clusters, inner, n_draws=200)
    g = row["size_matched_diff"]
    return None if np.isnan(g) else float(g)


def boot(model: str, which: str, n_boot: int = 2000) -> None:
    folds = [2, 3] if which == "23" else [int(which)]
    frames = [frame(model, f) for f in folds]
    kept0 = frames[0][frames[0]["no_history"] == 0]
    users = kept0["user_id"].drop_duplicates().tolist()
    for other in frames[1:]:
        if set(other.loc[other["no_history"] == 0, "user_id"]) != set(users):
            raise SystemExit("folds 2 and 3 do not share the same nonempty-window learners")
    lists = [user_lists(df, users) for df in frames]
    rng = np.random.default_rng([SEED, folds[0]])
    values, invalid = [], 0
    n = len(users)
    for b in range(n_boot):
        pick = rng.integers(0, n, size=n)
        gaps = []
        for user_s, user_d in lists:
            inner = np.random.default_rng(int(rng.integers(0, 2**31 - 1)))
            gaps.append(replicate_gap(user_s, user_d, pick, inner))
        if any(g is None for g in gaps):
            invalid += 1
            continue
        values.append(float(np.mean(gaps)))
        if (b + 1) % 250 == 0:
            print(f"{model} {which} {b + 1}/{n_boot}", flush=True)
    lo, hi = np.percentile(values, [2.5, 97.5])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"boot_{model}_{which}.json").write_text(
        json.dumps({"model": model, "partition": which, "n_learners": n, "n_used": len(values),
                    "n_invalid": invalid, "ci_low": float(lo), "ci_high": float(hi),
                    "seed": [SEED, folds[0]], "B": n_boot, "inner": 200}, indent=1),
        encoding="utf-8",
    )
    print(f"{model} {which} CI [{lo:.4f}, {hi:.4f}] invalid {invalid}", flush=True)


def combine() -> None:
    rows = []
    for model, label in (("dkt", "DKT"), ("tktc", "T-KT masked")):
        pts = pd.read_csv(OUT / f"points_{model}.csv").set_index("fold")
        units = {
            "fold 0": (pts.loc[0, "gap"], pts.loc[0, "n_focal"], pts.loc[0, "ci_low"], pts.loc[0, "ci_high"], 0, "primary"),
        }
        for which, label_p, folds in (("1", "fold 1", [1]), ("23", "folds 2–3", [2, 3]), ("4", "fold 4", [4])):
            b = json.loads((OUT / f"boot_{model}_{which}.json").read_text(encoding="utf-8"))
            g = float(np.mean([pts.loc[f, "gap"] for f in folds]))
            nf = float(np.mean([pts.loc[f, "n_focal"] for f in folds]))
            units[label_p] = (g, nf, b["ci_low"], b["ci_high"], b["n_invalid"], "supplementary")
        for part, (g, nf, lo, hi, inv, role) in units.items():
            rows.append({"model": label, "partition": part, "n_sparse": nf, "G": g, "ci_low": lo,
                         "ci_high": hi, "n_invalid": inv, "role": role})
        gs = np.array([units[k][0] for k in ("fold 0", "fold 1", "folds 2–3", "fold 4")])
        rows.append({"model": label, "partition": "four-partition mean ± SD", "n_sparse": np.nan,
                     "G": gs.mean(), "ci_low": np.nan, "ci_high": gs.std(ddof=1), "n_invalid": np.nan,
                     "role": "Table 5 check (ci_high column holds the SD)"})
    out = pd.DataFrame(rows)
    out.to_csv(RESULT, index=False)
    print(out.round(4).to_string())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1]
    if cmd == "points":
        points(sys.argv[2])
    elif cmd == "boot":
        boot(sys.argv[2], sys.argv[3])
    else:
        combine()
