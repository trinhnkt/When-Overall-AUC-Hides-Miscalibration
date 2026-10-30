"""Review items 1 and 7 after reading the code (30/10 21:30). No number changed; changed runs are red. Dry run unless --write.
 1. III.F: say exactly what the archived per-partition audit computes (p0_si_s10_leakage.py: L1, L4, L7 from split files;
    L2, L3, L5, L6 are fixed PASS entries for the pipeline code). Replaces the wording of c6_review_fixes.py.
 7. III.C: T-KT masked has no positional encoding (protocol_v2.TKTc: embedding -> TransformerEncoder with causal mask).
"""
import sys
from msedit import apply, sub

SUBS = [
    ("Table 3 reports the outcomes",
     "The archived audit covers the partition files and the training and scoring code of the locally implemented "
     "models (DKT and T-KT masked); simpleKT reads",
     "The archived audit computes L1, L4, and L7 from the split files of each partition; L2, L3, L5, and L6 are "
     "properties of the pipeline code (fitted values use training rows only, the KC map is static, no calibration "
     "map is fitted, checkpoints are selected on validation data) and were recorded from the code, not recomputed "
     "per partition. simpleKT reads"),
    ("Table 2 lists the runs",
     "with a causal mask and padding id 2n (n is the number of KCs).",
     "with a causal mask, no positional encoding (order enters only through the mask), and padding id 2n "
     "(n is the number of KCs)."),
]

def edit(body, path):
    for prefix, old, new in SUBS:
        sub(body, prefix, old, new, allow_flatten=True)

if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
