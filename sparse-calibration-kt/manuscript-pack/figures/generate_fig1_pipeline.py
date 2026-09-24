#!/usr/bin/env python3
"""Fig. 1: compact L1–L7 pipeline. Tags match Table 3; order is workflow."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
OUT = HERE / "fig1_pipeline.png"

NAVY = "#1F3A5F"
INK = "#222222"
LINE = "#4A4A4A"
TAG = "#0D5C63"
FILL_L = "#EEF4F6"
FILL_U = "#F3F3F3"

ROW1 = [
    ("Raw logs", None),
    ("Preprocess", "L2"),
    ("Split", "L1"),
    ("KC map", "L3"),
    ("Train-only\nfrequency", None),
]
ROW2 = [
    ("KC strata", "L4"),
    ("Cold-start", "L7"),
    ("No test-based\nselection", "L6"),
    ("ECE / Brier", "L5"),
    ("Reliability\n+ report", None),
]


def box(ax, x, y, w, h, title: str, tag: str | None) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.008,rounding_size=0.018",
            linewidth=0.85,
            edgecolor=NAVY,
            facecolor=FILL_L if tag else FILL_U,
        )
    )
    if tag:
        ax.text(
            x + w / 2,
            y + h * 0.68,
            title,
            ha="center",
            va="center",
            fontsize=7.4 if "No test-based" in title else 8.2,
            fontname="Times New Roman",
            color=INK,
            linespacing=1.05,
        )
        ax.text(
            x + w / 2,
            y + h * 0.28,
            f"[{tag}]",
            ha="center",
            va="center",
            fontsize=7.2,
            fontname="Times New Roman",
            color=TAG,
            fontweight="bold",
        )
    else:
        ax.text(
            x + w / 2,
            y + h / 2,
            title,
            ha="center",
            va="center",
            fontsize=7.4 if "No test-based" in title else 8.2,
            fontname="Times New Roman",
            color=INK,
            linespacing=1.05,
        )


def arrow(ax, x1, y1, x2, y2) -> None:
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=0.85,
            color=LINE,
            shrinkA=0,
            shrinkB=0,
        )
    )


def main() -> None:
    fig, ax = plt.subplots(figsize=(6.97, 2.42), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    n = 5
    w, h = 0.168, 0.34
    gap = (1 - n * w) / (n + 1)
    y1, y2 = 0.56, 0.08
    xs = [gap + i * (w + gap) for i in range(n)]
    for i, ((title, tag), x) in enumerate(zip(ROW1, xs)):
        box(ax, x, y1, w, h, title, tag)
        if i < n - 1:
            arrow(ax, x + w + 0.004, y1 + h / 2, xs[i + 1] - 0.004, y1 + h / 2)
    rail_y = (y1 + y2 + h) / 2
    xr = xs[-1] + w / 2
    xl = xs[0] + w / 2
    ax.plot([xr, xr], [y1, rail_y], color=LINE, linewidth=0.85, solid_capstyle="round")
    ax.plot([xr, xl], [rail_y, rail_y], color=LINE, linewidth=0.85, solid_capstyle="round")
    arrow(ax, xl, rail_y, xl, y2 + h + 0.004)
    for i, ((title, tag), x) in enumerate(zip(ROW2, xs)):
        box(ax, x, y2, w, h, title, tag)
        if i < n - 1:
            arrow(ax, x + w + 0.004, y2 + h / 2, xs[i + 1] - 0.004, y2 + h / 2)
    ax.text(
        0.5,
        0.955,
        "Workflow order  ·  L-tags match Table 3 (not left-to-right numbering)",
        ha="center",
        va="center",
        fontsize=7.0,
        fontname="Times New Roman",
        color=NAVY,
    )
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.05, facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
