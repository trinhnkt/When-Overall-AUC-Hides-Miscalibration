"""A4 (Table 6 and new Table 7) and C1 (new Table A5) manuscript edits."""
from __future__ import annotations

import copy
import json
import sys

import pandas as pd

from msedit import RES, W, apply, fill_table, find_para, fmt, rewrite, set_text, sub, table_after, table_rows
from table6_context import table6_rows, table7_rows

CTX = json.loads((RES / "TABLE6_7_CONTEXT.json").read_text(encoding="utf-8"))
C1 = pd.read_csv(RES / "C1_PARTITION_INTERVALS.csv")

T6_CAPTION = (
    "Table 6. Estimability and evidence status by dataset under the primary protocol. Checks are those of Table 3. "
    "Direction refers to ΔECE (5), the size-matched gap G (9), and the bias reference ΔECE* (7); for Junyi Academy the "
    "medium group takes the place of the sparse group. Counts and descriptors are in Table 7."
)
T7_CAPTION = (
    "Table 7. Counts and structural descriptors by dataset. Train-derived rows use the fold-0 training split and the KCs "
    "present in it; test-derived rows are mean counts over the four unique partitions of the split files (KC-level rows for "
    "XES3G5M), except the primary-protocol sparse N, which counts nonempty windows as in Table 5. ρ is Spearman’s "
    "correlation with log(1 + ftrain). Support: R, Reliable; L, Limited; I, Insufficient. XES3G5M is descriptive only."
)
A5_CAPTION = (
    "Table A5. Size-matched gap G (9) and its learner-cluster 95% interval by unique partition (ASSISTments 2012, primary "
    "protocol; B = 2,000, inner draws 200). Fold 0 is the primary uncertainty analysis. The other intervals are supplementary, "
    "use a generator seeded [20261021, f] for the first fold f of the partition, and are not combined into one significance "
    "claim. For folds 2–3, each replicate resamples the shared learners once and averages G over the two runs. The mean ± SD "
    "rows reproduce Table 5."
)
A5_HEADER = ["Model", "Partition", "N sparse", "G", "95% interval", "Role"]


def a5_rows() -> list[list[str]]:
    rows = []
    for _, r in C1.iterrows():
        if r["partition"].startswith("four"):
            rows.append([r["model"], "Mean ± SD", "", f"{fmt(r['G'], 4)} ± {fmt(r['ci_high'], 4)}", "", "Table 5"])
        else:
            rows.append([r["model"], r["partition"], str(int(round(r["n_sparse"]))), fmt(r["G"], 4),
                         f"{fmt(r['ci_low'], 4)} to {fmt(r['ci_high'], 4)}",
                         "Primary" if r["role"] == "primary" else "Supplementary"])
    return rows


def insert_copy_after(body, caption_prefix: str, new_caption_start: str):
    """Copy the caption paragraph and table that follow caption_prefix; insert the copy after that table."""
    cap, tbl = table_after(body, caption_prefix)
    new_cap, new_tbl = copy.deepcopy(cap), copy.deepcopy(tbl)
    set_text(new_cap, new_caption_start)
    tbl.addnext(new_cap)
    new_cap.addnext(new_tbl)
    spacer = copy.deepcopy(cap)
    for t in spacer.iter(W + "t"):
        t.text = ""
    tbl.addnext(spacer)


IVC_1 = (
    "Whether a sparse contrast can be estimated is a property of the counts (Tables 6 and 7; RQ2). ASSISTments 2012 has a "
    "nonempty sparse group. Under the primary protocol its mean sparse N is {n}, which is Limited, and its dense group is "
    "Reliable, so the contrast is eligible. Junyi Academy has no sparse group; the post-hoc contrast is medium versus dense, "
    "and the medium group is Reliable. XES3G5M has low-frequency KC rows ({xes_sp} sparse test rows on average), but the "
    "model contrast is not eligible: check L8 failed, and the dataset is descriptive only. Strict cold-start and very-sparse "
    "groups are not given a primary ECE."
)
IVC_2 = (
    "The structural descriptors in Table 7 characterize the datasets, and none of them is treated as a necessary or "
    "sufficient condition for the direction of a contrast. Frequency and difficulty were negatively correlated on "
    "ASSISTments 2012 (ρ = {a}, with sparse KCs harder) and Junyi Academy (ρ = {j}) but weakly positively correlated on "
    "XES3G5M (ρ = {x})."
)


def edit(body, path) -> None:
    fill_table(body, "Table 6.", T6_CAPTION, ["Question", "ASSISTments 2012", "Junyi Academy", "XES3G5M"],
               table6_rows(table_rows(body, "Table 5."), C1))
    insert_copy_after(body, "Table 6.", "Table 7.")
    fill_table(body, "Table 7.", T7_CAPTION, ["Quantity", "ASSISTments 2012", "Junyi Academy", "XES3G5M"], table7_rows(CTX))
    insert_copy_after(body, "Table A4.", "Table A5.")
    fill_table(body, "Table A5.", A5_CAPTION, A5_HEADER, a5_rows(), weights=[1.4, 1.2, 1.0, 1.0, 1.6, 1.2])

    t7 = {r[0]: r for r in table7_rows(CTX)}
    rewrite(body, "Whether a sparse contrast can be estimated",
            IVC_1.format(n=t7["Mean sparse N, primary protocol"][1].split(" ")[0],
                         xes_sp=t7["Sparse-group test rows (E2)"][3].split(" ")[0]))
    rewrite(body, "The structural descriptors in Table 6",
            IVC_2.format(a=t7["Frequency–difficulty ρ"][1], j=t7["Frequency–difficulty ρ"][2],
                         x=t7["Frequency–difficulty ρ"][3].lstrip("+")))
    sub(body, "KT models, however, are usually compared", "(Section IV.C)", "(Table 7)")
    sub(
        body,
        "The 95% interval is the fold-0 learner-cluster bootstrap.",
        "under NumPy’s linear percentile.",
        "under NumPy’s linear percentile. As a supplementary analysis, the same procedure was applied to fold 1, folds 2–3, "
        "and fold 4, with a generator seeded [20261021, f] for the first fold f of each partition; for folds 2–3, each "
        "replicate resamples the shared learners once, computes G on both runs with separate inner seeds, and stores their "
        "mean (Table A5).",
    )
    sub(
        body,
        "On ASSISTments 2012, under protocol",
        "It is not a test of the other partitions, and ΔECE* is not that interval.",
        "It is not a test of the other partitions, and ΔECE* is not that interval. Table A5 gives G and the same "
        "learner-cluster interval for each unique partition; for both models every interval excludes 0, but these "
        "supplementary intervals are not combined into one significance claim.",
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for r in table7_rows(CTX):
        print(" | ".join(r))
    for r in a5_rows():
        print(" | ".join(r))
    apply(edit, "--write" in sys.argv)
