# B7 Obsolete text and long captions

Date: 2026-10-29

Status: PASS

Script: `scripts/b7_text_cleanup.py --write` (named and both blind copies). `scripts/fmt_check.py` found no new loss of italic, bold, or sub/superscript formatting.

## 1. Junyi unmasked T-KT alignment text in III.B

Removed during A3 ("The Junyi Academy runs of the Transformer model (T-KT, Section III.C) were aligned differently…"). The B7 script stops if that text reappears; it did not. The only remaining Junyi T-KT mention is the Limitations sentence "Junyi T-KT was not retrained with a mask", which states an exclusion.

## 2. Fig. 3 caption

Now two sentences: "Fig. 3. ASSISTments 2012, primary protocol, fold 0: reliability diagrams for DKT (left) and T-KT masked (right), 15 equal-width bins, nonempty windows. Sparse group N = 430 (Limited); dense group N = 521,348 (Reliable)." The dense N is the fold-0 nonempty-window count from `results/A3_far_fold0.csv` and Table A3. The interpretation (no checkpoint attribution, Junyi and XES3G5M not plotted) moved to the IV.B paragraph that introduces Fig. 3. The plotted image was not regenerated; any title text inside the image must be checked by eye (A6).

## 3. Table 5 caption

Now: protocol identification, column definitions (ΔECE (5), ΔECE* (7), G (9), fold-0 learner-cluster interval), support labels, and the Junyi medium-group note. Removed: the repeated "not a confidence interval or a test", "not a result for every partition", "not attributed to the checkpoint alone", and the XES3G5M sentence, which are in the Methods and Discussion.

## 4. XES3G5M technical claims

| Claim | Evidence | Action |
| --- | --- | --- |
| "the windows repeat responses at some boundaries" (IV.B) | `P0_IJIET_FINAL_CORRECTION_2026/artifact_final/04_audits/GATE_B_XES_REPORT.md`, section "Window boundary": 301 train/valid responses recur in a later window of the same learner; learner 2108, fold 0, example | Rewritten with the count and an explicit pointer to the audit (artifact v4, audits/GATE_B_XES_REPORT.md) |
| 863,807 second and later KC rows by the release's repeat flags (III.A) | `manuscript-pack/analysis/xes_padding_counts.csv`, row `is_repeat_nonzero,863807` | Kept; pointer added (artifact v4, audits/xes_padding_counts.csv) |
| 18,066 students, 7,652 questions, 865 KCs, 5,549,635 interactions (III.A) | dataset paper [27] | Already cited |
| L8 failure route (III.A) | same GATE_B report and the code audit in III.A | Unchanged |

Both audit files are added to artifact v4 under `audits/` in the artifact update of this batch.
