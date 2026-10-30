"""B2: redraw Fig. 3 with the title 'ASSISTments 2012, primary protocol, fold 0' and swap it into the three manuscripts.

Plot code is the write_fig3 routine of scripts/p0_gate_d_rebuild.py (not re-run); only the title and the
thousands separator in the legend counts differ. Pass --write to replace word/media/image3.png.
"""
from __future__ import annotations

import hashlib
import os
import sys
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from msedit import PATHS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.ece_uncertainty import ece  # noqa: E402

PRED = ROOT / "results" / "predictions"
OUT = Path(__file__).resolve().parents[1] / "results" / "fig3_primary_protocol_fold0.png"
MEDIA = "word/media/image3.png"
OLD_SHA = "db13b34afa33"
SPECS = [
    ("pred_assist2012_dkt_best_validxchunk_fold0_42.csv.gz", "DKT"),
    ("pred_assist2012_tktc_best_validxchunk_fold0_42.csv.gz", "T-KT masked"),
]
EXPECTED = {("DKT", "sparse"): (430, 0.0916), ("DKT", "dense"): (521348, 0.0070),
            ("T-KT masked", "sparse"): (430, 0.0951), ("T-KT masked", "dense"): (521348, 0.0120)}


def bin_curve(y, p, n_bins=15):
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    conf, acc = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p <= hi) if lo == 0 else (p > lo) & (p <= hi)
        if not np.any(mask):
            continue
        conf.append(float(np.mean(p[mask])))
        acc.append(float(np.mean(y[mask])))
    return np.array(conf), np.array(acc)


def draw() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3), sharex=True, sharey=True)
    colors = {"dense": "#1f4e79", "sparse": "#c0392b"}
    for ax, (name, title) in zip(axes, SPECS):
        frame = pd.read_csv(PRED / name, usecols=["y", "p", "group", "no_history"])
        kept = frame[frame["no_history"] == 0]
        ax.plot([0, 1], [0, 1], ls="--", c="0.55", lw=0.8)
        for group in ("dense", "sparse"):
            sub = kept[kept["group"] == group]
            y = sub["y"].to_numpy()
            p = sub["p"].to_numpy(dtype=float)
            e = ece(y, p)
            n_exp, e_exp = EXPECTED[(title, group)]
            assert len(y) == n_exp and round(e, 4) == e_exp, (title, group, len(y), e)
            conf, acc = bin_curve(y, p)
            ax.plot(conf, acc, marker="o", ms=3.5, lw=1.2, color=colors[group],
                    label=f"{group}  ECE {e:.4f}  N {len(y):,}")
        ax.set_title(title, fontsize=10)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Mean predicted probability")
        ax.legend(fontsize=7, frameon=False, loc="upper left")
        ax.grid(alpha=0.25, lw=0.4)
    axes[0].set_ylabel("Observed frequency")
    fig.suptitle("ASSISTments 2012, primary protocol, fold 0", fontsize=10)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200)
    plt.close(fig)


def swap(path: Path, png: bytes) -> None:
    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        assert hashlib.sha256(src.read(MEDIA)).hexdigest().startswith(OLD_SHA), path
        for item in src.infolist():
            dst.writestr(item, png if item.filename == MEDIA else src.read(item.filename))
    os.replace(tmp, path)
    print("UPDATED", path.name)


if __name__ == "__main__":
    draw()
    print("wrote", OUT, hashlib.sha256(OUT.read_bytes()).hexdigest())
    if "--write" in sys.argv:
        for p in PATHS:
            swap(p, OUT.read_bytes())
