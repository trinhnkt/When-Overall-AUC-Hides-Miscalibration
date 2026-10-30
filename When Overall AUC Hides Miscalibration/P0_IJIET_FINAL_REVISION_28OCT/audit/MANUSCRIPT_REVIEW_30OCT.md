# Full manuscript review (30 Oct 2026, after the numeric audit)

Reviewed: clean blind copy, every paragraph and table. Numbers: no mismatch (see FULL_TEXT_AUDIT_30OCT.md). No text was changed. Findings are wording, notation, and consistency items for the authors to decide.

1. Section III.F, Table 3 caption: "the three local models" is never defined, and Table 2's third model is simpleKT, which the next sentence treats as not covered. Name the models (probably ASSISTments DKT, T-KT masked, Junyi DKT).
2. Section III.E (size-matched gap paragraph and the interval paragraph): "N_sparse" and "ECE_sparse" appear with literal underscores, while the rest of the paper uses subscripts (Nsparse, ECEsparse).
3. Table A2: leftover column "reason missing = none" although the caption says no cell is missing. Removing the column changes no value.
4. Data and Code Availability mentions "an additional run (fold 5)", but Section III.B defines only folds 0-4. Either explain in one clause or drop the mention (the authors' choice; it is a transparency statement).
5. Section IV.A last sentence ("These figures are not benchmark scores from a different split.") is unclear.
6. Table 1 test events (e.g., 534,150 for ASSISTments) differ from N in Tables 4-5 (523,612) because rows with empty history are excluded; a short caption note would prevent a reader's question.
7. Table 2 / Section III.C do not say whether T-KT masked uses positional encoding; I found none in baseline_runner.py or protocol_v2.py. Confirm and state it.
8. Section III.E is very dense (random-number-generator details). Consider moving the stage-by-stage description to an appendix or the artifact README; keep the definition of G and the interval.
9. Introduction says miscalibration can show up as overconfidence; ECE is unsigned, and the excess-FAR evidence (Table A3) has no interval. Keep "can", or add a signed-calibration statement.
Strengths: claims are scoped to one dataset; bias reference and matched gap are kept apart; limitations are explicit; every number traces to prediction files.

UPDATE 21:2x: items 1, 2, 3, 5, 6 fixed (c6_review_fixes.py). Item 1 wording asserts that the archived audit covers the code of DKT and T-KT masked; the authors should confirm. Items 4, 7, 8, 9 open.

UPDATE 21:24: item 4 (fold 5) fixed by c7_fold5.py. Item 8 (Section III.E density): author decision - leave as is, the text is correct. Open: 1 (author confirmation of what the L1-L7 audit covers), 7 (positional encoding), 9 (optional).

UPDATE 21:24: item 9 (word 'overconfidence' in the Introduction): author decision - keep, acceptable because the sentence says 'can'. Open: 1 (what the L1-L7 audit covers), 7 (positional encoding).

UPDATE 21:3x: items 1 and 7 resolved from the code (c8_items1_7.py). Table 3 per-partition values were cross-checked with si_s10_leakage.csv (L7 empty/I pattern, n_strict_test, Junyi sparse empty). Open only: author confirmation that the new III.F wording is acceptable.
