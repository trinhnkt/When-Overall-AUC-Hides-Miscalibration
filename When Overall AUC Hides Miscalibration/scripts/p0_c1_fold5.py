#!/usr/bin/env python3
"""C1: one new ASSISTments learner partition, then the primary-protocol models.

Shuffle seed 2028. Fold index 5. Does not overwrite folds 0-4.
Fold 3 stays the duplicate of fold 2. Init seed for the three models is 42.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FOLD = 5
SHUFFLE_SEED = 2028
INIT_SEED = 42
DATASET = "assist2012"


def existing_test_users() -> list[set]:
    sets = []
    for fold in range(5):
        path = ROOT / f"data/processed/{DATASET}/splits/learner_based/fold_{fold}/test.csv"
        sets.append(set(pd.read_csv(path, usecols=["user_id"])["user_id"]))
    return sets


def create_split() -> None:
    out = ROOT / f"data/processed/{DATASET}/splits/learner_based/fold_{FOLD}"
    if (out / "test.csv").is_file():
        print(f"SPLIT exists {out}", flush=True)
        return
    frame = pd.read_csv(ROOT / f"data/processed/{DATASET}/interactions.csv")
    users = list(frame["user_id"].dropna().unique())
    np.random.seed(SHUFFLE_SEED)
    np.random.shuffle(users)
    n_test = int(len(users) * 0.2)
    n_valid = int(len(users) * 0.1)
    test_users = set(users[:n_test])
    valid_users = set(users[n_test : n_test + n_valid])
    train_users = set(users[n_test + n_valid :])
    prior = existing_test_users()
    # Fold 2 and fold 3 are the same partition, so compare with folds 0, 1, 2, 4.
    for fold in (0, 1, 2, 4):
        if test_users == prior[fold]:
            raise SystemExit(f"new test users match fold {fold}")
    out.mkdir(parents=True, exist_ok=True)
    for name, chosen in ("train", train_users), ("valid", valid_users), ("test", test_users):
        part = frame[frame["user_id"].isin(chosen)]
        dest = out / f"{name}.csv"
        part.to_csv(dest, index=False)
        print(f"WROTE {dest.name} rows={len(part)} users={len(chosen)}", flush=True)


def distinct_report() -> None:
    sets = existing_test_users()
    new = set(pd.read_csv(
        ROOT / f"data/processed/{DATASET}/splits/learner_based/fold_{FOLD}/test.csv",
        usecols=["user_id"],
    )["user_id"])
    labels = []
    for fold, users in enumerate(sets):
        same = [i for i, other in enumerate(sets) if other == users]
        labels.append(same[0])
    print(f"old fold identity {labels}", flush=True)
    for fold in (0, 1, 2, 4):
        print(f"overlap fold{fold} {len(new & sets[fold])}", flush=True)
    if any(new == sets[fold] for fold in (0, 1, 2, 4)):
        raise SystemExit("new partition is not distinct")
    print("C1_SPLIT = PASS", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    create_split()
    distinct_report()
    from scripts.p0_b1_tktc_assist import run_one as train_tktc
    from scripts.p0_b3_simplekt_assist import run_one as train_simplekt
    from scripts.p0_c1_dkt import run_one as train_dkt

    train_dkt(FOLD, INIT_SEED, 50)
    train_tktc(FOLD, INIT_SEED, 50)
    train_simplekt(FOLD, INIT_SEED, 50, 8, 24, 1e-3)
    print("C1 QUEUE DONE", flush=True)


if __name__ == "__main__":
    main()
