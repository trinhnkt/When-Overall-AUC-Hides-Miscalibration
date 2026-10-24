#!/usr/bin/env python3
"""A2 gate. The locking commit must predate every new A3–A5 result file."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
GIT_ROOT = PROJECT.parent
PLAN_PATH = "sparse-calibration-kt/docs/analysis_plan_P0_v2.md"
PLAN_SHA = "46e0208d0fcd3d03d880449e5a6fdd2643619ee0"
REQUIRED = (
    "ECE_sparse",
    "ASSISTments 2012",
    "compute_ece",
    "src/calibration_eval.py",
    "best_valid",
    "no_history = 0",
    "fold 0",
    "bốn phân hoạch",
    "ECE_sweep",
    "p = 0.5",
    "final",
    "chunk",
    "slide",
    "R1.",
    "R2.",
    "R3.",
    "R4.",
    "R5.",
    "R6.",
    "R7.",
    "R8.",
    "XES3G5M",
    "T-KT-c",
)


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=GIT_ROOT, text=True, encoding="utf-8"
    ).strip()


def main() -> None:
    failures: list[str] = []
    head = git("rev-parse", PLAN_SHA)
    if head != PLAN_SHA:
        failures.append(f"plan sha resolved to {head}")
    touched = git("log", "-1", "--format=%H", "--", PLAN_PATH)
    if touched != PLAN_SHA:
        failures.append(f"latest plan commit is {touched}, not the locking commit")
    committed_at = datetime.fromisoformat(git("log", "-1", "--format=%cI", PLAN_SHA))
    blob = git("show", f"{PLAN_SHA}:{PLAN_PATH}")
    missing = [token for token in REQUIRED if token not in blob]
    if missing:
        failures.append("locked plan missing: " + ", ".join(missing))
    print(f"analysis_plan_commit {PLAN_SHA}")
    print(f"committed_at {committed_at.isoformat()}")

    result_files = list((PROJECT / "runs" / "a_dkt").rglob("train_log.csv"))
    result_files += list((PROJECT / "results" / "predictions").glob("pred_assist2012_dkt_*.csv.gz"))
    if not result_files:
        failures.append("no A3–A5 result file to compare")
        first = None
    else:
        first = min(result_files, key=lambda path: path.stat().st_mtime)
        first_at = datetime.fromtimestamp(first.stat().st_mtime).astimezone()
        print(f"first_result {first.name}")
        print(f"first_result_at {first_at.isoformat()}")
        if committed_at >= first_at:
            failures.append("analysis plan commit is not earlier than the first result")
        else:
            print("timestamp order: plan commit < first result")

    manifest = pd.read_csv(PROJECT / "runs" / "manifest.csv", dtype=str, keep_default_na=False)
    bad = manifest.loc[
        ~manifest["analysis_plan_commit"].str.startswith("46e0208"),
        "run_id",
    ].tolist()
    if bad:
        failures.append("manifest analysis_plan_commit mismatch: " + ", ".join(bad))
    else:
        print(f"manifest rows {len(manifest)} all cite 46e0208")

    if failures:
        print("A2 = FAIL")
        for item in failures:
            print(f"FAIL {item}")
        sys.exit(1)
    print("A2 = PASS")


if __name__ == "__main__":
    main()
