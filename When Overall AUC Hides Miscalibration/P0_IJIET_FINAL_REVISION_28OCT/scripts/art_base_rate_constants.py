"""Write results/base_rate_constants.csv: the constant p of each IRT rerun file used as the Table A1 base-rate reference.

The IRT files (Junyi about 3.3 GB) are not shipped; this file records the constant, the source hash, and the learner check.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PRED = HERE.parents[1] / "results" / "predictions"
OUT = HERE.parent / "results" / "base_rate_constants.csv"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    rows = []
    for dataset in ("assist2012", "junyi"):
        for fold, seed in PAIRS:
            irt_name = f"{dataset}_learner_based_irt_1pl_seed{seed}_predictions_rerun.csv"
            dkt_name = f"pred_{dataset}_dkt_best_validxchunk_fold{fold}_{seed}.csv.gz"
            irt = pd.read_csv(PRED / irt_name, usecols=["user_id", "p_pred"])
            rate = irt["p_pred"].unique()
            if np.ptp(rate) > 1e-12:
                raise SystemExit(f"{irt_name}: prediction is not constant")
            same = set(irt["user_id"].unique()) == set(pd.read_csv(PRED / dkt_name, usecols=["user_id"])["user_id"].unique())
            if not same:
                raise SystemExit(f"{irt_name}: test learners differ from {dkt_name}")
            rows.append({"dataset": dataset, "fold": fold, "seed": seed, "p_base": repr(float(rate[0])),
                         "irt_source": f"results/predictions/{irt_name}", "irt_rows": len(irt),
                         "irt_sha256": sha256(PRED / irt_name), "applied_to": dkt_name,
                         "same_test_learners": same})
            print(f"{dataset} fold{fold} p_base={float(rate[0])!r}", flush=True)
    OUT.parent.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print("WROTE", OUT)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
