"""B7: shorten Fig. 3 and Table 5 captions; source the XES3G5M technical claims."""
from __future__ import annotations

import sys

from msedit import apply, find_para, rewrite, sub, text_of

FIG3 = (
    "Fig. 3. ASSISTments 2012, primary protocol, fold 0: reliability diagrams for DKT (left) and T-KT masked (right), "
    "15 equal-width bins, nonempty windows. Sparse group N = 430 (Limited); dense group N = 521,348 (Reliable)."
)
TABLE5 = (
    "Table 5. Calibration by frequency group under the primary protocol (mean ± SD across four unique partitions; N is the "
    "mean count). ΔECE is (5), ΔECE* is the bias reference (7), and the matched gap is G (9); the 95% CI is the fold-0 "
    "learner-cluster interval of G. Support: Limited if 100 ≤ N < 1,000; Reliable if N ≥ 1,000. Junyi Academy is post-hoc, "
    "and its medium group takes the place of the sparse group."
)


def edit(body, path) -> None:
    if "aligned differently" in text_of(find_para(body, "Deep models were trained with seeds")):
        raise SystemExit("Junyi T-KT alignment text still in III.B")
    rewrite(body, "Fig. 3. Reliability diagrams", FIG3)
    rewrite(body, "Table 5. Calibration under protocol", TABLE5)
    sub(
        body,
        "Fig. 3 shows the fold-0 reliability diagrams",
        "They are visual checks, not the four-partition estimate.",
        "They are visual checks, not the four-partition estimate, and they do not show that a checkpoint removed or caused "
        "the difference. Junyi Academy has no sparse group and XES3G5M is descriptive only, so neither is plotted.",
    )
    sub(
        body,
        "Junyi Academy has no sparse group. Its DKT medium-versus-dense",
        "XES3G5M has no model row. Check L8 failed, the windows repeat responses at some boundaries, and no corrected model "
        "was trained. Its frequency distribution remains a descriptive audit.",
        "XES3G5M has no model row: check L8 failed (Section III.A), and no corrected model was trained. Our audit of the "
        "released question-level sequence files also found 301 training responses repeated at the start of the learner’s "
        "next window (artifact v4, audits/GATE_B_XES_REPORT.md). Its frequency distribution remains descriptive only.",
    )
    sub(
        body,
        "XES3G5M was loaded from the authors’ KC-level release",
        "(863,807 rows by the release’s repeat flags, 13.5% of the file)",
        "(863,807 rows by the release’s repeat flags, 13.5% of the file; counted in artifact v4, audits/xes_padding_counts.csv)",
    )


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
