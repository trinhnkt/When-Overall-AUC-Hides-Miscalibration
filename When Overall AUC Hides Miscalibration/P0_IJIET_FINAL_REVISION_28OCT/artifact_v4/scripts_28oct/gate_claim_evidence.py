"""Write docs/CLAIM_EVIDENCE_P4.csv: each conclusion in the Abstract, Section I, V.A, and the Conclusion mapped to its evidence.

Every 'quote' must occur verbatim in all three manuscript copies; otherwise the script exits 1. The values themselves
are checked by artifact_v4/rebuild/reproduce_tables.py, b3_rq3_from_table_a2.py, and table6_context.py --check.
"""
from __future__ import annotations

import csv
import sys

from msedit import PATHS, dump

R28 = PATHS[0].parents[2] / "P0_IJIET_FINAL_REVISION_28OCT"
OUT = R28 / "docs" / "CLAIM_EVIDENCE_P4.csv"
PRIMARY = "primary protocol (P0-BV200-15EW): best validation AUC, windows <= 200, 15 equal-width bins, no_history = 0"
GRID = "Table A2 grid: {final, best validation} x {full history, window 200}; 15 bins"
DKT = "artifact_v4/predictions/pred_assist2012_dkt_best_validxchunk_fold{0..4}_*.csv.gz"
TKT = "artifact_v4/predictions/pred_assist2012_tktc_best_validxchunk_fold{0..4}_*.csv.gz"
DKT4 = "artifact_v4/predictions/pred_assist2012_dkt_{final,best_valid}x{full,chunk}_fold{0..4}_*.csv.gz"
JUNYI = "artifact_v4/predictions/pred_junyi_dkt_best_validxchunk_fold{0..4}_*.csv.gz"
REPRO = "artifact_v4/rebuild/reproduce_tables.py (published_gap.py)"
CTX = "P0_IJIET_FINAL_REVISION_28OCT/results/TABLE6_7_CONTEXT.json"
CTXS = "P0_IJIET_FINAL_REVISION_28OCT/scripts/table6_context.py (--check: All values match)"
XES = "artifact_v4/audits/GATE_B_XES_REPORT.md; artifact_v4/audits/xes_padding_counts.csv"

# (id, section, quote, table, value, source, script, protocol)
CLAIMS = [
    ("ABS-1", "Abstract", "the mean expected calibration error (ECE) was 0.0982 on sparse KCs and 0.0089 on dense KCs, a difference of 0.0893",
     "Table 5", "0.0982; 0.0089; 0.0893", DKT, REPRO, PRIMARY),
    ("ABS-2", "Abstract", "the gap was 0.0400", "Table 5", "0.0400", DKT, REPRO, PRIMARY),
    ("ABS-3", "Abstract", "its learner-cluster 95% interval on one partition was 0.0170 to 0.0821", "Table 5; Table A5 (fold 0)",
     "0.0170; 0.0821", DKT + " (fold 0)", REPRO + " fold-0 bootstrap, seed 20261021, B = 2000", PRIMARY),
    ("ABS-4", "Abstract", "A causally masked Transformer showed the same direction, with a difference of 0.1041", "Table 5", "0.1041",
     TKT, REPRO, PRIMARY),
    ("ABS-5", "Abstract", "lower by 0.0181 to 0.0774 than the final checkpoint", "Table A2", "0.0181; 0.0774", DKT4,
     REPRO + "; P0_IJIET_FINAL_REVISION_28OCT/scripts/b3_rq3_from_table_a2.py -> results/B3_TABLE_A2_EFFECTS.csv", GRID),
    ("ABS-6", "Abstract", "changing the test window shifted it by −0.0131 to +0.0068", "Table A2", "−0.0131; +0.0068", DKT4,
     "P0_IJIET_FINAL_REVISION_28OCT/scripts/b3_rq3_from_table_a2.py -> results/B3_TABLE_A2_EFFECTS.csv", GRID),
    ("ABS-7", "Abstract", "a mean of 398 sparse responses per partition", "Table 5", "398", DKT, REPRO + " (rounded count check)", PRIMARY),
    ("ABS-8", "Abstract", "Junyi Academy had no sparse group", "Table 6; Table 7", "sparse test rows: empty", CTX + "; " + JUNYI, CTXS,
     "train-count groups, learner-based fold 0 split"),
    ("I-1", "Section I", "18.9% of the KCs in ASSISTments 2012 and 21.5% of the XES3G5M KCs present in training had fewer than 100 training rows",
     "Table 7", "18.9%; 21.5%", CTX, CTXS, "train-count groups, learner-based fold 0 split"),
    ("I-2", "Section I", "Across four unique partitions their sparse ECE exceeds their dense ECE", "Table 5; Table A2 (best/200 column)",
     "DKT ΔECE 0.0893; T-KT masked ΔECE 0.1041", DKT + "; " + TKT,
     REPRO + "; per-partition values in P0_IJIET_FINAL_REVISION_28OCT/results/C1/points_{dkt,tktc}.csv", PRIMARY),
    ("I-3", "Section I", "The size-matched gap is positive, and the fold-0 interval for that gap excludes 0", "Table 5; Table A5",
     "G 0.0400 and 0.0581; fold-0 intervals 0.0170 to 0.0821 and 0.0233 to 0.0878", DKT + "; " + TKT, REPRO, PRIMARY),
    ("I-4", "Section I", "ΔECE* does not stay positive on every partition", "Table A2 (ΔECE* column); Table 5",
     "DKT ΔECE* −0.0081; T-KT masked ΔECE* 0.0068", DKT + "; " + TKT,
     REPRO + "; P0_IJIET_FINAL_REVISION_28OCT/results/C1/points_{dkt,tktc}.csv (column star)", PRIMARY),
    ("I-5", "Section I", "For RQ2, Junyi Academy has no sparse group", "Table 6; Table 7", "sparse test rows: empty", CTX, CTXS,
     "train-count groups"),
    ("I-6", "Section I", "check L8 failed and no corrected model was trained, so it is a descriptive audit only", "Table 3; Table 6",
     "L8 FAIL", XES, "audit report (no model run)", "not evaluated"),
    ("I-7", "Section I", "the validation-AUC checkpoint was associated with a ΔECE lower by 0.0181 to 0.0774", "Table A2",
     "0.0181; 0.0774", DKT4, "P0_IJIET_FINAL_REVISION_28OCT/scripts/b3_rq3_from_table_a2.py", GRID),
    ("I-8", "Section I", "changed ΔECE by −0.0131 to +0.0068", "Table A2", "−0.0131; +0.0068", DKT4,
     "P0_IJIET_FINAL_REVISION_28OCT/scripts/b3_rq3_from_table_a2.py", GRID),
    ("I-9", "Section I", "Two runs on one learner partition differ by up to 0.0268", "Table A2 (final/full, folds 2 and 3)",
     "0.1354 − 0.1086 = 0.0268", DKT4, "P0_IJIET_FINAL_REVISION_28OCT/scripts/b3_rq3_from_table_a2.py", GRID),
    ("VA-1", "V.A", "Both primary models showed the difference; its observed magnitude differed between them", "Table 5; Table A5",
     "ΔECE 0.0893 vs 0.1041; G 0.0400 vs 0.0581", DKT + "; " + TKT, REPRO, PRIMARY),
    ("VA-2", "V.A", "DKT and T-KT masked have a positive raw ΔECE and a positive size-matched gap", "Table 5", "0.0893, 0.1041; 0.0400, 0.0581",
     DKT + "; " + TKT, REPRO, PRIMARY),
    ("VA-3", "V.A", "The fold-0 interval for that gap excludes 0", "Table 5", "0.0170 to 0.0821; 0.0233 to 0.0878", DKT + "; " + TKT,
     REPRO, PRIMARY),
    ("VA-4", "V.A", "ΔECE* does not exclude a small-sample explanation on every partition", "Table A2; Table 5", "ΔECE* positive only on fold 1 (DKT)",
     DKT, REPRO, PRIMARY),
    ("VA-5", "V.A", "Its post-hoc ΔECE* is −0.0032", "Table 5", "−0.0032", JUNYI, REPRO, PRIMARY + "; Junyi medium vs dense, post-hoc"),
    ("VA-6", "V.A", "XES3G5M is a descriptive audit only", "Table 4; Table 6", "Not evaluated", XES, "audit report (no model run)", "not evaluated"),
    ("CON-1", "Conclusion", "The observed magnitude differed between the two primary models and across checkpoints, partitions, and datasets",
     "Table 5; Table A2; Table A5", "see VA-1, I-7, Table A5 G 0.0295 to 0.0834", DKT4 + "; " + TKT + "; " + JUNYI,
     REPRO + "; rebuild/partition_intervals.py", PRIMARY + "; Table A2 grid"),
    ("CON-2", "Conclusion", "DKT and a causally masked Transformer show a higher sparse ECE than dense ECE", "Table 5",
     "0.0982 > 0.0089; 0.1199 > 0.0158", DKT + "; " + TKT, REPRO, PRIMARY),
    ("CON-3", "Conclusion", "The fold-0 size-matched interval excludes 0", "Table 5", "0.0170 to 0.0821; 0.0233 to 0.0878",
     DKT + "; " + TKT, REPRO, PRIMARY),
    ("CON-4", "Conclusion", "ΔECE* is −0.0081 for DKT and 0.0068 for the masked Transformer", "Table 5", "−0.0081; 0.0068",
     DKT + "; " + TKT, REPRO, PRIMARY),
    ("CON-5", "Conclusion", "its post-hoc ΔECE* is −0.0032", "Table 5", "−0.0032", JUNYI, REPRO, PRIMARY + "; post-hoc"),
    ("CON-6", "Conclusion", "XES3G5M is a descriptive audit only, with no model-based result", "Table 4; Table 6", "Not evaluated", XES,
     "audit report (no model run)", "not evaluated"),
]


def main() -> int:
    texts = [" ".join(dump(p)) for p in PATHS]
    bad = 0
    rows = []
    for cid, section, quote, table, value, source, script, protocol in CLAIMS:
        found = all(quote in t for t in texts)
        bad += not found
        rows.append({"claim_id": cid, "section": section, "claim_text": quote, "table": table, "value": value,
                     "prediction_or_summary_source": source, "script": script, "protocol": protocol,
                     "text_in_all_three_copies": "YES" if found else "NO"})
        print(f"{'PASS' if found else 'FAIL'} {cid} {quote[:70]}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"WROTE {OUT} ({len(rows)} claims, {bad} not found)")
    return bad


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(1 if main() else 0)
