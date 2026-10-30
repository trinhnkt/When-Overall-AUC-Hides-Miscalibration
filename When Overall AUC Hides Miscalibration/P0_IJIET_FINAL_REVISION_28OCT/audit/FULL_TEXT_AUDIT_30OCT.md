# Full-text audit against experimental results (30 Oct 2026)

Scope: the clean blind manuscript (`a6_clean/manuscript-pack_manuscript_blind_A6_clean.docx`; the other two clean copies have identical text) was checked paragraph by paragraph and table by table. No manuscript text was changed by this audit.

## Method
1. Full recomputation in a temporary copy of artifact v4: `py -3 rebuild/reproduce_tables.py` (folds 0-4 from prediction exports; about 12 minutes). Result: 303 PASS lines, 0 FAIL, "PASS all supported table checks". Covers Tables 4, 5, A1, A2, A3, A4 and the G column of A5 (DKT, T-KT masked, Junyi DKT, simpleKT).
2. `scripts/full_text_audit.py` maps every printed table cell to a recomputed check and classifies every number in the prose (TABLE / CONTEXT / CONST / OPEN). 165 printed values looked up; the 28 reported "problems" are formatting artefacts only (integer 430.0 vs 430, A3 caption values, A4 summary row, Junyi fold-0 gap 0.0085 which is in the Table 5 text but not in A5). 51 OPEN prose numbers were traced by hand (below).
3. `scripts/full_text_qualitative.py`: sign, direction and count claims from the prediction files and results CSVs. FAILS: [].
4. `table6_context.py --check`: All values match. `b1_abstract.py --check`, `b2_notation.py --check`: pass. `check_blind.py` on the three clean copies: pass, P0-BV200 appears once.

## OPEN prose numbers traced by hand
- Table A2 ranges (printed cells): checkpoint effect 0.0181-0.0774 overall, 0.0217-0.0774 (window 200), 0.0181-0.0729 (full history); window shift -0.0131 to +0.0068; folds 2 vs 3 final/full 0.0268. All reproduced from the recomputed A2 cells.
- FAR 0.215 / 0.179 / 0.036 [-0.041, 0.125] and T-KT 0.232 / 0.182 / 0.051 [-0.019, 0.141]: PASS in the A3 recomputation.
- ECE0(415)=0.095, ECE0(523,971)=0.003: 0.5*sqrt(15/N) = 0.0951 and 0.0027.
- Table 1 / Section III.B counts: ASSISTments 2,657,490 rows, 27,806 learners, 265 KCs; Junyi 16,215,567 rows, 71,014 learners, 1,326 KCs (`results/tables/dataset_stats.csv`); about 12,200 responses per exercise = 16,215,567 / 1,326 = 12,229; XES3G5M 6,413,353 rows (`audits/xes_padding_counts.csv`), 863,807 repeat-flag rows = 13.47% (13.5% in text), 301 repeated training responses (GATE_B report); fold-0 test events 1,282,422 (XES) and 3,269,022 (Junyi) found in the run manifests.
- Table 2 hyperparameters vs code (`baseline_runner.py`, `p0_retrain_official_simplekt.py`): DKT embedding 64, LSTM hidden 128, 1 layer; T-KT d=64, 4 heads, 2 layers; batch 64; Adam lr 1e-3; up to 50 epochs, patience 8; simpleKT d=256, 2 blocks, 8 heads, batch 24. All match. DKT pads with token 0 (collate uses padding_value 0) and T-KT uses padding id 2n, as written in III.C.
- External figures (checked against the sources, not the experiments): pyKT 8.38 and 13.09 points; XES3G5M 18,066 students, 7,652 questions, 865 KCs, 5,549,635 interactions, MIT license; Junyi CC BY-NC-SA 4.0 and Kaggle citation for [26]; commit 46e0208 dated 21 Oct 2026.

## Result
No mismatch between the manuscript text and the experimental results was found. Remaining caveats are unrelated to numbers: author sign-off, supervisor confirmation of C2, Funding statement, ethics document name.
Scratch files `results/_full_audit_pre.txt` / `_post.txt` removed; full audit output kept in `audit/FULL_TEXT_AUDIT_30OCT_output.txt`.

## Addendum 30 Oct 2026, 21:4x (after the review edits)
- Artifact v4 integrity: all 219 files in MANIFEST.csv match their sha256 (0 bad, 0 missing).
- Figures read from the final clean docx: Fig. 3 (fold 0) dense/sparse ECE 0.0070/0.0916 (DKT) and 0.0120/0.0951 (T-KT masked), N 521,348 / 430, recomputed from the fold-0 prediction files and equal to the figure; Fig. 2 KC counts per group equal Table 7 (ASSISTments 11/39/68/147; Junyi 0/0/33/1,293; XES3G5M 62/122/172/498 plus 11 KCs with ftrain = 0); Fig. 1 tags L1-L8 match III.F.
- Protocol constants in code: M = 15 equal-width bins, ECE0 = 0.5*sqrt(M/N), R = 2000 draws, B = 2000 with 200 inner draws, seed 20261021, tau = 0.7, cut points 20/100/500.
- Table 3 per-partition values equal manuscript-pack/analysis/si_s10_leakage.csv.
- Re-run after the edits: full_text_audit (165 printed values, same 28 formatting-only items), qualitative claims (no failures), b1/b2/table6_context checks, check_blind: all pass. No mismatch.
