"""Write one scored file in the P-2 schema and append runs/manifest.csv.

Does not train a model. Callers pass a frame that already contains the
scored columns. Missing checkpoints are recorded as NOT RECOVERED and are
not filled in.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = ROOT / "results" / "predictions"
MANIFEST = ROOT / "runs" / "manifest.csv"

COLUMNS = [
    "dataset",
    "split",
    "partition_id",
    "init_seed",
    "model",
    "protocol",
    "run_id",
    "row_index",
    "event_id",
    "user_id",
    "seq_pos",
    "history_len",
    "no_history",
    "item_id",
    "kc_id",
    "f_train",
    "group",
    "y",
    "p",
]

MANIFEST_COLUMNS = [
    "run_id",
    "dataset",
    "partition_id",
    "init_seed",
    "model",
    "protocol",
    "code_commit",
    "analysis_plan_commit",
    "config_path",
    "checkpoint_path",
    "selected_epoch",
    "train_log",
    "pred_file",
    "pred_sha256",
    "n_rows",
    "status",
    "notes",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def prediction_name(dataset, model, protocol, partition, seed) -> str:
    protocol = str(protocol).replace("×", "x").replace(" ", "")
    return f"pred_{dataset}_{model}_{protocol}_{partition}_{seed}.csv.gz"


def write_prediction(frame: pd.DataFrame, dest: Path) -> Path:
    missing = [col for col in COLUMNS if col not in frame.columns]
    if missing:
        raise SystemExit(f"prediction frame missing {missing}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    frame.loc[:, COLUMNS].to_csv(dest, index=False, compression="gzip")
    return dest


def append_manifest(row: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    extra = [key for key in row if key not in MANIFEST_COLUMNS]
    if extra:
        raise SystemExit(f"unknown manifest columns {extra}")
    line = {key: row.get(key, "") for key in MANIFEST_COLUMNS}
    new = pd.DataFrame([line])
    if MANIFEST.exists():
        old = pd.read_csv(MANIFEST)
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(MANIFEST, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--partition", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--status", default="LEGACY")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    frame = pd.read_csv(args.source)
    dest = PRED_DIR / prediction_name(
        args.dataset, args.model, args.protocol, args.partition, args.seed
    )
    write_prediction(frame, dest)
    append_manifest({
        "run_id": dest.stem,
        "dataset": args.dataset,
        "partition_id": args.partition,
        "init_seed": args.seed,
        "model": args.model,
        "protocol": args.protocol,
        "pred_file": str(dest.relative_to(ROOT)).replace("\\", "/"),
        "pred_sha256": sha256(dest),
        "n_rows": len(frame),
        "status": args.status,
        "notes": args.notes,
    })
    print(dest)


if __name__ == "__main__":
    main()
