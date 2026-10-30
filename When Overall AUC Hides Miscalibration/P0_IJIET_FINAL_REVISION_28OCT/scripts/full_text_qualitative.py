"""Check the sign / direction / count claims in the prose against the per-partition results.
Reads prediction exports (artifact_v4/predictions), results/*.csv; prints PASS/FAIL per claim."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

R28 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R28 / "artifact_v4" / "rebuild"))
from published_gap import ece, ece0_bound  # noqa: E402

PRED = R28 / "artifact_v4" / "predictions"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
fails = []


def claim(label: str, ok: bool, detail: str = "") -> None:
    print(("PASS" if ok else "FAIL"), label, detail)
    if not ok:
        fails.append(label)


def unit(values: dict[int, float]) -> list[float]:
    return [values[0], values[1], 0.5 * (values[2] + values[3]), values[4]]


def per_fold(model: str) -> dict[str, dict[int, float]]:
    out = {"delta": {}, "star": {}}
    for fold, seed in PAIRS:
        df = pd.read_csv(PRED / f"pred_assist2012_{model}_best_validxchunk_fold{fold}_{seed}.csv.gz",
                         usecols=["y", "p", "group", "no_history"])
        df = df[df["no_history"] == 0]
        sp, de = df[df["group"] == "sparse"], df[df["group"] == "dense"]
        d = ece(sp["y"].to_numpy(), sp["p"].to_numpy(float)) - ece(de["y"].to_numpy(), de["p"].to_numpy(float))
        out["delta"][fold] = d
        out["star"][fold] = d - ece0_bound(len(sp))
    return out


def main() -> int:
    for model, label in (("dkt", "DKT"), ("tktc", "T-KT masked")):
        pf = per_fold(model)
        delta, star = unit(pf["delta"]), unit(pf["star"])
        print(label, "delta by unit", [round(x, 4) for x in delta], "star by unit", [round(x, 4) for x in star])
        claim(f"{label}: sparse ECE above dense ECE on every unique partition (ΔECE>0)", all(x > 0 for x in delta))
        pos = [i for i, x in enumerate(star) if x > 0]
        names = ["fold 0", "fold 1", "folds 2-3", "fold 4"]
        print("  star positive on", [names[i] for i in pos])
        if label == "DKT":
            claim("DKT: ΔECE* positive only on fold 1", pos == [1])
        else:
            claim("T-KT masked: ΔECE* positive on fold 1 and fold 4 only", pos == [1, 3])

    ci = pd.read_csv(R28 / "results" / "C1_PARTITION_INTERVALS.csv")
    ci = ci[ci["partition"].astype(str).str.startswith("fold")]
    print("C1 rows", len(ci), sorted(set(ci.partition)))
    for model, g in ci.groupby("model"):
        claim(f"{model}: matched gap positive on all four partitions", bool((g["G"] > 0).all()))
        claim(f"{model}: every per-partition interval excludes 0", bool((g["ci_low"] > 0).all()))
        claim(f"{model}: no invalid bootstrap replicates", bool((g["n_invalid"] == 0).all()))

    b5 = pd.read_csv(R28 / "results" / "B5_STRATIFIED_METRICS.csv")
    a = b5[(b5.dataset == "assist2012") & (b5.role == "primary") & pd.to_numeric(b5.fold, errors="coerce").notna()]
    print("B5 models", sorted(set(a.model)), "groups", sorted(set(a.group)), "folds", sorted(set(a.fold)))
    for model in ("DKT", "T-KT masked"):
        m = a[a.model == model]
        if m.empty:
            print("no rows for", model, sorted(set(a.model)))
            continue
        ov = m[m.group == "overall"].set_index("fold")["AUC"]
        sp = m[m.group == "sparse"].set_index("fold")["AUC"]
        rel_s = m[m.group == "sparse"].set_index("fold")["REL"]
        rel_d = m[m.group == "dense"].set_index("fold")["REL"]
        higher = [int(f) for f in sp.index if sp[f] > ov[f]]
        lower = [int(f) for f in sp.index if sp[f] < ov[f]]
        print(model, "sparse AUC above overall in folds", higher, "below in folds", lower)
        if model == "DKT":
            claim("DKT: sparse-group AUC exceeded overall AUC in every run", len(lower) == 0)
        else:
            claim("T-KT masked: sparse AUC lower than overall in folds 1 and 4 (as stated)", {1, 4} <= set(lower), f"lower in {lower}")
        claim(f"{model}: REL larger on sparse than dense in every run", bool((rel_s > rel_d.reindex(rel_s.index)).all()))

    far = pd.read_csv(R28 / "results" / "A3_far_partitions.csv")
    for model, g in far.groupby("model"):
        d = g.set_index("fold")["DeltaFAR"]
        units = [d[0], d[1], 0.5 * (d[2] + d[3]), d[4]]
        print(model, "ΔFAR by unit", [round(x, 3) for x in units])
        claim(f"{model}: ΔFAR positive in 3 of 4 unique partitions", sum(x > 0 for x in units) == 3)
        claim(f"{model}: ΔFAR mean/range", True, f"mean {np.mean(units):.3f} sd {np.std(units, ddof=1):.3f} range {min(units):.3f} to {max(units):.3f}")

    ctx = (R28 / "results" / "TABLE6_7_CONTEXT.json").read_text(encoding="utf-8")
    print("context json length", len(ctx))
    print("FAILS:", fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
