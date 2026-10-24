#!/usr/bin/env python3
"""A3 gate. Builds the window table from prediction files. Does not edit them.

Version-I DKT checkpoints are not on disk, so this gate cannot return PASS.
It returns PARTIAL_NOT_RECOVERED when the unit tests pass and the table is
computed from retrained files, or FAIL when a test fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from scripts.p0_retrain_official_simplekt import simplekt_no_history  # noqa: E402
from src.ece_uncertainty import ece, ece0_bound  # noqa: E402
from tests.test_protocol_v2 import (  # noqa: E402
    test_ut_w1_and_w2_chunk_matches_and_counts_no_history,
    test_ut_w2_full_and_slide_count_learners_and_chunk_counts_chunks,
)

PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
MODES = ("full", "chunk", "slide")
SELECTS = ("final", "best_valid")
OUT = PROJECT / "results" / "tables" / "p0_a3_window_context.csv"
BAN_I_DENSE = 0.0602
BAN_I_SPARSE = 0.2333
TOLERANCE = 0.0005


def one_row(frame: pd.DataFrame) -> dict:
    kept = frame[frame["no_history"] == 0]
    row = {
        "partition": str(frame["partition_id"].iloc[0]),
        "protocol": str(frame["protocol"].iloc[0]),
    }
    for group in ("dense", "sparse"):
        part = kept[kept["group"] == group]
        flagged = frame[(frame["group"] == group) & (frame["no_history"] == 1)]
        row[f"N_{group}"] = int(len(part))
        row[f"ECE_{group}"] = ece(part["y"].to_numpy(), part["p"].to_numpy(dtype=float)) if len(part) else float("nan")
        row[f"n_no_history_{group}"] = int(len(flagged))
    row["DeltaECE"] = row["ECE_sparse"] - row["ECE_dense"]
    row["DeltaECE_star"] = row["DeltaECE"] - ece0_bound(row["N_sparse"])
    return row


def simplekt_rule_holds() -> None:
    frame = pd.DataFrame({
        "user_id": [1, 1, 1, 1, 1, 2],
        "timestamp": [0, 1, 2, 3, 4, 0],
        "correct": [0, 1, 0, 1, 0, 1],
    })
    flags = simplekt_no_history(frame, seq_len=3)
    assert list(flags.tolist()) == [1, 0, 0, 1, 0, 1]


def main() -> None:
    failures: list[str] = []
    try:
        test_ut_w1_and_w2_chunk_matches_and_counts_no_history()
        print("UT-W1 PASS")
    except Exception as exc:
        failures.append(f"UT-W1 {exc}")
        print("UT-W1 FAIL")
    try:
        test_ut_w2_full_and_slide_count_learners_and_chunk_counts_chunks()
        print("UT-W2 PASS")
    except Exception as exc:
        failures.append(f"UT-W2 {exc}")
        print("UT-W2 FAIL")
    try:
        simplekt_rule_holds()
        print("simpleKT no_history rule PASS")
    except Exception as exc:
        failures.append(f"simpleKT no_history {exc}")
        print("simpleKT no_history rule FAIL")

    rows = []
    files = sorted((PROJECT / "results" / "predictions").glob("pred_assist2012_dkt_*x*_fold*_*.csv.gz"))
    present = set()
    for path in files:
        frame = pd.read_csv(path, usecols=["partition_id", "protocol", "group", "no_history", "y", "p", "init_seed"])
        rows.append(one_row(frame))
        present.add((str(frame["partition_id"].iloc[0]), str(frame["protocol"].iloc[0])))
        print(f"READ {path.name} DeltaECE={rows[-1]['DeltaECE']:.4f}", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(rows, columns=[
        "partition", "protocol", "N_dense", "N_sparse", "ECE_dense", "ECE_sparse",
        "DeltaECE", "DeltaECE_star", "n_no_history_dense", "n_no_history_sparse",
    ])
    table.to_csv(OUT, index=False)
    print(f"WROTE {OUT} rows={len(table)}")

    missing = []
    for fold, seed in PAIRS:
        for select in SELECTS:
            for mode in MODES:
                protocol = f"{select}x{mode}"
                key = (f"fold{fold}", protocol)
                if key not in present:
                    missing.append(f"fold{fold}_seed{seed}_{protocol}")
    if missing:
        print("MISSING " + ", ".join(missing))
    else:
        print("five runs x full/chunk/slide x final/best_valid are on disk")

    print("Version-I DKT checkpoints NOT_RECOVERED")
    print(
        "REPRODUCTION of ECE_dense 0.0602 and ECE_sparse 0.2333 was not attempted; "
        f"tolerance {TOLERANCE} is unused. Targets {BAN_I_DENSE} and {BAN_I_SPARSE} were not written into the table."
    )
    if failures:
        print("A3 = FAIL")
        for item in failures:
            print(f"FAIL {item}")
        sys.exit(1)
    print("A3 = PARTIAL_NOT_RECOVERED")


if __name__ == "__main__":
    main()
