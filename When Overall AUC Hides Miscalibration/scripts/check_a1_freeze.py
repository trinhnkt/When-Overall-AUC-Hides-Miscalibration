#!/usr/bin/env python3
"""A1 gate. Prints A1 = PASS only when the freeze and export checks hold.

Group sizes are reported. A difference from Table 5 is not rewritten.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
GIT_ROOT = PROJECT.parent
BAN_I = "f5b5d58cbc5f797e225700debd0177ce49f8bc7c"
PRED_COLUMNS = [
    "dataset", "split", "partition_id", "init_seed", "model", "protocol",
    "run_id", "row_index", "event_id", "user_id", "seq_pos", "history_len",
    "no_history", "item_id", "kc_id", "f_train", "group", "y", "p",
]
MANIFEST_COLUMNS = [
    "run_id", "dataset", "partition_id", "init_seed", "model", "protocol",
    "code_commit", "analysis_plan_commit", "config_path", "checkpoint_path",
    "selected_epoch", "train_log", "pred_file", "pred_sha256", "n_rows",
    "status", "notes",
]
MANUSCRIPT_N = {"dense": 523971, "medium": 5963, "sparse": 415}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=GIT_ROOT, text=True).strip()


def bucket(freq: int) -> str:
    if freq == 0:
        return "strict_cold_start"
    if freq < 20:
        return "very_sparse"
    if freq < 100:
        return "sparse"
    if freq < 500:
        return "medium"
    return "dense"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stratum_counts(fold: int) -> dict[str, int]:
    split = PROJECT / "data" / "processed" / "assist2012" / "splits" / "learner_based" / f"fold_{fold}"
    train = pd.read_csv(split / "train.csv", usecols=["kc_id"])
    test = pd.read_csv(split / "test.csv", usecols=["kc_id"])
    counts = train["kc_id"].value_counts()
    groups = test["kc_id"].map(counts).fillna(0).astype(int).map(bucket)
    return groups.value_counts().to_dict()


def main() -> None:
    failures: list[str] = []
    tag = git("rev-parse", "P0-ban-I")
    archival = git("rev-parse", "archival/ban-I")
    branch = git("branch", "--show-current")
    print(f"tag P0-ban-I {tag}")
    print(f"branch archival/ban-I {archival}")
    print(f"current branch {branch}")
    if tag != BAN_I or archival != BAN_I:
        failures.append("ban-I tag or archival branch is not f5b5d58")
    if branch != "exp/p0-bo-sung":
        failures.append(f"current branch is {branch}, expected exp/p0-bo-sung")
    listed = set(git("tag", "--list").splitlines())
    if "P0-ban-I" not in listed:
        failures.append("git tag --list does not show P0-ban-I")

    env = (PROJECT / "env.txt").read_text(encoding="utf-8")
    for token in ("python", "torch", "cuda", "pykt", "gpu", "os "):
        if token not in env.lower():
            failures.append(f"env.txt missing {token.strip()}")
    lock = PROJECT / "requirements-lock.txt"
    if not lock.is_file() or lock.stat().st_size < 100:
        failures.append("requirements-lock.txt missing or empty")

    manifest_path = PROJECT / "runs" / "manifest.csv"
    manifest = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
    missing_manifest = [col for col in MANIFEST_COLUMNS if col not in manifest.columns]
    if missing_manifest:
        failures.append(f"manifest missing {missing_manifest}")
    print("manifest columns OK" if not missing_manifest else f"manifest missing {missing_manifest}")
    print(f"manifest rows {len(manifest)}")

    preds = sorted((PROJECT / "results" / "predictions").glob("pred_assist2012_dkt_*.csv.gz"))
    if not preds:
        failures.append("no pred_assist2012_dkt_*.csv.gz export")
    else:
        sample = preds[0]
        frame = pd.read_csv(sample, nrows=5)
        missing_pred = [col for col in PRED_COLUMNS if col not in frame.columns]
        print(f"sample {sample.name}")
        print("prediction columns OK" if not missing_pred else f"prediction missing {missing_pred}")
        if missing_pred:
            failures.append(f"prediction missing {missing_pred}")

    ckpt_dir = PROJECT / "results" / "checkpoints"
    present = sorted(p.name for p in ckpt_dir.glob("*.pt")) if ckpt_dir.is_dir() else []
    ban_i_dkt = [name for name in present if "assist2012" in name and "dkt" in name and "a9_" not in name]
    print(f"checkpoint pt files on disk: {len(present)}")
    print("ban-I ASSISTments DKT weights: " + ("FOUND " + ",".join(ban_i_dkt) if ban_i_dkt else "NOT_RECOVERED"))
    print("other pt files are not ban-I DKT/T-KT and are not used to fill that gap")

    per_fold = {fold: stratum_counts(fold) for fold in (0, 1, 2, 3, 4)}
    # Four unique partitions: fold 2 and fold 3 share one split, so average them first.
    shared = {
        name: (per_fold[2].get(name, 0) + per_fold[3].get(name, 0)) / 2
        for name in ("dense", "medium", "sparse")
    }
    four = []
    for name in ("dense", "medium", "sparse"):
        values = [per_fold[0][name], per_fold[1][name], shared[name], per_fold[4][name]]
        four.append((name, sum(values) / 4, values))
    print("four-partition mean test rows by train-only stratum (fold 2 and 3 averaged first):")
    for name, mean, values in four:
        target = MANUSCRIPT_N[name]
        print(f"  {name} mean={mean:.2f} manuscript={target} delta={mean - target:.2f} folds={values}")
        if abs(mean - target) >= 1:
            print(f"  DISCREPANCY {name}: computed mean {mean:.2f} vs manuscript {target}")

    # One new export, fold 0, is not the four-partition manuscript mean.
    if preds:
        full = pd.read_csv(preds[0], usecols=["group", "no_history"])
        kept = full[full["no_history"] == 0]
        print(f"new export {preds[0].name} rows={len(full)} no_history={int((full['no_history']==1).sum())}")
        for name in ("dense", "medium", "sparse"):
            observed = int((kept["group"] == name).sum())
            print(f"  new {name} no_history=0 N={observed} manuscript_mean={MANUSCRIPT_N[name]}")

    if failures:
        print("A1 = FAIL")
        for item in failures:
            print(f"FAIL {item}")
        sys.exit(1)
    print("A1 = PASS")


if __name__ == "__main__":
    main()
