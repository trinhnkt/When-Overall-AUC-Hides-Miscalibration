#!/usr/bin/env python3
"""A2B remaining pipeline: neural train → eval → A9 → manifest.

Writes only under IJIET_FINAL_REVISION/a2b/ and the revision analysis/audit folders.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable


def run(args: list[str]) -> None:
    print(">>", " ".join(args), flush=True)
    subprocess.check_call(args)


def main() -> None:
    run([PY, "-u", str(HERE / "train_models.py"), "--model", "dkt"])
    run([PY, "-u", str(HERE / "train_models.py"), "--model", "simplekt"])
    run([PY, "-u", str(HERE / "evaluate.py")])
    run([PY, "-u", str(HERE / "train_a9.py")])
    run([PY, "-u", str(HERE / "analyze_a9.py")])
    run([PY, "-u", str(HERE / "write_manifest.py")])
    print("A2B rest complete", flush=True)


if __name__ == "__main__":
    main()
