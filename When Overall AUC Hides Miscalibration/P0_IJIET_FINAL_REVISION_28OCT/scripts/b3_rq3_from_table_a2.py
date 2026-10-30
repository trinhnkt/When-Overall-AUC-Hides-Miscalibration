"""B3: checkpoint and window effects from Table A2; rewrite IV.D and the RQ3 answer."""
from __future__ import annotations

import sys
import zipfile

import pandas as pd
from lxml import etree

from msedit import PATHS, RES, W, apply, find_para, fmt, rewrite, sub, table_rows

with zipfile.ZipFile(PATHS[1]) as z:
    BODY = etree.fromstring(z.read("word/document.xml")).find(W + "body")
rows = table_rows(BODY, "Table A2.")
head = rows[0]
grid = pd.DataFrame(
    [[r[0]] + [float(x.replace("−", "-")) for x in r[1:5]] for r in rows[1:]],
    columns=["run", "final_full", "final_200", "best_full", "best_200"],
)
grid["ckpt_200"] = grid["best_200"] - grid["final_200"]
grid["ckpt_full"] = grid["best_full"] - grid["final_full"]
grid["win_final"] = grid["final_200"] - grid["final_full"]
grid["win_best"] = grid["best_200"] - grid["best_full"]
grid.round(4).to_csv(RES / "B3_TABLE_A2_EFFECTS.csv", index=False)

ckpt = pd.concat([grid["ckpt_200"], grid["ckpt_full"]])
win = pd.concat([grid["win_final"], grid["win_best"]])
red_lo, red_hi = -ckpt.max(), -ckpt.min()
win_lo, win_hi = win.min(), win.max()
f2 = grid.set_index("run").loc["fold 2"]
f3 = grid.set_index("run").loc["fold 3"]
init = (f2[["final_full", "final_200", "best_full", "best_200"]] - f3[["final_full", "final_200", "best_full", "best_200"]]).abs()

CHECKS = [
    ("checkpoint-associated reduction low", fmt(red_lo, 4), "0.0181"),
    ("checkpoint-associated reduction high", fmt(red_hi, 4), "0.0774"),
    ("window-associated change low", fmt(win_lo, 4), "−0.0131"),
    ("window-associated change high", fmt(win_hi, 4), "0.0068"),
    ("initialization difference final/full", fmt(init["final_full"], 4), "0.0268"),
    ("initialization max cell", init.idxmax(), "final_full"),
    ("checkpoint direction consistent", str(bool((ckpt < 0).all())), "True"),
]
R200 = (fmt(-grid["ckpt_200"].max(), 4), fmt(-grid["ckpt_200"].min(), 4))
RFULL = (fmt(-grid["ckpt_full"].max(), 4), fmt(-grid["ckpt_full"].min(), 4))
STAR = rows[1:]

IVD_TITLE = "D. Sensitivity to checkpoint and test window"
IVD = (
    "Table A2 is the ASSISTments DKT grid of checkpoint and test window; every cell is ΔECE, and no cell is missing. "
    "At a fixed test window, the validation-AUC checkpoint had a lower ΔECE than the final checkpoint in all five runs. "
    f"This checkpoint-associated difference ranged from 0.0181 to 0.0774 ({R200[0]} to {R200[1]} with windows of 200 and "
    f"{RFULL[0]} to {RFULL[1]} with the full history). At a fixed checkpoint, the window-associated change (window 200 minus "
    "full history) ranged from −0.0131 to +0.0068 and had no consistent sign. The two runs that share one learner partition "
    "(folds 2 and 3) differ by up to 0.0268 in the final/full cell, which exceeds the smallest checkpoint-associated "
    "differences. The direction of the checkpoint-associated difference was therefore consistent across the reported runs, "
    "but its magnitude comes from one model on one dataset and is not a general causal estimate. Final × full versus "
    "validation × window 200 changes both factors and is not assigned to either alone. Raw ΔECE stays positive in every "
    "cell; ΔECE* in the primary cell is positive only in fold 1. Alternative frequency cut points were not evaluated under "
    "this protocol."
)
RQ3_OLD = (
    "For RQ3, the DKT grid in Table A2 separates the final checkpoint from the validation-AUC checkpoint and the full test "
    "history from windows of 200. Changing both at once is not attributed to either factor alone."
)
RQ3_NEW = (
    "For RQ3, in the DKT grid of Table A2 the validation-AUC checkpoint was associated with a ΔECE lower by 0.0181 to 0.0774 "
    "than the final checkpoint at a fixed test window, in every reported run, whereas changing the window at a fixed "
    "checkpoint changed ΔECE by −0.0131 to +0.0068. Two runs on one learner partition differ by up to 0.0268, so these are "
    "checkpoint-associated differences for one model and dataset, not a general causal estimate."
)


def edit(body, path) -> None:
    rewrite(body, "D. Checkpoint and test-window sensitivity", IVD_TITLE)
    rewrite(body, "Table A2 is the ASSISTments DKT grid", IVD)
    sub(body, "For RQ1, DKT and a causally masked", RQ3_OLD, RQ3_NEW)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(grid.round(4).to_string())
    print("primary-cell ΔECE*:", [r[5] for r in STAR])
    bad = 0
    for label, got, want in CHECKS:
        ok = got == want
        bad += not ok
        print(f"{'PASS' if ok else 'FAIL'} {label}: computed {got} reported {want}")
    if bad:
        raise SystemExit("B3 range check failed")
    print(IVD)
    print(RQ3_NEW)
    apply(edit, "--write" in sys.argv)
