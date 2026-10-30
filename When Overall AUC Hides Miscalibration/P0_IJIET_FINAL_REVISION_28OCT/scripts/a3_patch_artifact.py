"""Add the Tables A1/A3/A4 recompute to artifact v4 and refresh MANIFEST hashes in place."""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a5_build_artifact as b  # noqa: E402


def main() -> None:
    b.rebuild_files()
    b.statistics()
    b.write_readme()
    art = b.ART
    path = art / "MANIFEST.csv"
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    seen = set()
    for row in body:
        file = art / row[0]
        seen.add(row[0])
        if not file.is_file():
            raise SystemExit(f"MISSING {row[0]}")
        size, digest = str(file.stat().st_size), b.sha256(file)
        if (row[1], row[2]) != (size, digest):
            print(f"UPDATED {row[0]}")
            row[1], row[2] = size, digest
    new = "rebuild/far_brier.py"
    if new not in seen:
        file = art / new
        body.insert(
            next(i for i, r in enumerate(body) if r[0] == "rebuild/published_gap.py"),
            [new, str(file.stat().st_size), b.sha256(file), "recompute command",
             "P0_IJIET_FINAL_REVISION_28OCT/scripts/a5_far_brier.py",
             "FAR and Brier decomposition for Tables A1, A3, A4"],
        )
        print(f"ADDED {new}")
    out = io.StringIO()
    writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(body)
    path.write_text(out.getvalue(), encoding="utf-8")
    print(f"MANIFEST {len(body)} files")


if __name__ == "__main__":
    main()
