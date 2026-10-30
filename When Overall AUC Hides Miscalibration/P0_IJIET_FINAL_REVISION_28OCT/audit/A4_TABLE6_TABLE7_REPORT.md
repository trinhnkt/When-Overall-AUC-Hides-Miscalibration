# A4 Table 6 and Table 7 for RQ2

Date: 2026-10-29

Status: PASS

## Scripts

- `scripts/table6_context.py`: recomputes every Table 7 value from `data/processed/{assist2012,junyi,xes3g5m}/splits/learner_based/fold_{0..4}` and writes `results/TABLE6_7_CONTEXT.json`. `--check` builds the expected Table 6 and Table 7 rows and asserts them against all three manuscript copies. Output of the last run: `All values match`.
- `scripts/a4_c1_edit_manuscript.py --write`: rewrote Table 6, inserted Table 7 after it, rewrote IV.C, and changed the Introduction pointer "(Section IV.C)" to "(Table 7)".

There was no earlier `scripts/table6_context.py` in the repository. It was created here.

## Table 6, "Estimability and evidence status by dataset under the primary protocol"

Rows: Sparse group present?; L1–L8 PASS?; Eligible model contrast?; Direction; Uncertainty; Protocol/evidence status. The caption now describes only these rows and points to Table 7 for counts. The old caption's "Part B", "IQR", and "structural context" text, which had no matching rows, is gone.

- L8 wording now matches Table 3: "L8 not applicable (one row per response)" for ASSISTments 2012 and Junyi; "L8 FAIL" for XES3G5M.
- XES3G5M cells: "KC-level tail only", "No", "Not evaluated", "Descriptive only".
- Junyi direction and uncertainty cells are read from the Table 5 Junyi row by the checker (ΔECE 0.0302, G 0.0115, ΔECE* −0.0032, interval 0.0010 to 0.0434).
- The ASSISTments uncertainty cell uses `results/C1_PARTITION_INTERVALS.csv`: every partition interval excludes 0.

## Table 7, counts and descriptors

| Quantity | Kind | ASSISTments 2012 | Junyi | XES3G5M | Definition |
| --- | --- | --- | --- | --- | --- |
| KCs present in training | train | 265 | 1,326 | 854 | fold-0 train rows, kc_id ≠ −1 |
| KCs with ftrain < 100 (E1) | train | 18.9% | 0.0% | 21.5% | share of KCs present in training |
| KCs very sparse / sparse / medium / dense | train | 11 / 39 / 68 / 147 | 0 / 0 / 33 / 1,293 | 62 / 122 / 172 / 498 | frequency distribution by group |
| Strict cold-start KCs in fold-0 test | train | 0 | 0 | 3 | test KCs absent from training |
| Median ftrain per KC | train | 988 | 7,074 | 1,002 | |
| Sparse-group test rows (E2) | test | 415 (L) | empty | 1,969 (R) | split files, mean over folds 0, 1, mean(2, 3), 4 |
| Very-sparse test rows | test | 17 (I) | empty | 114 (L) | same |
| Strict cold-start test rows | test | 1 (I; nonempty in 1 of 4) | empty | 5 (I; nonempty in 4 of 4) | same |
| Mean sparse N, primary protocol | test | 398 (L) | No sparse group | Not evaluated | `results/B5_STRATIFIED_METRICS.csv`, nonempty windows (Table 5 value 397.75) |
| Frequency–difficulty ρ | structural | −0.241 | −0.416 | +0.110 | Spearman, log(1 + ftrain) vs 1 − mean training correctness |
| Median item support | structural | 32 (dense 198; sparse 1) | 18 (dense 18) | 3 (dense 9; sparse 1) | distinct items per KC |
| Frequency–position ρ | structural | −0.326 | −0.324 | −0.126 | Spearman, log(1 + ftrain) vs median normalized sequence position |

Folds 2 and 3 share test learners in all three datasets (checked by the script), so they are averaged first.

## Values that changed from the earlier Table 6 (commit 0dceec0)

| Quantity | Earlier | Now | Reason |
| --- | --- | --- | --- |
| ASSISTments frequency–difficulty ρ | −0.227 | −0.241 | The earlier value reproduces only from `manuscript-pack/analysis/regression_unit_audit.csv`, the KC set of the removed unmasked T-KT regression (260 KCs, −0.2274). Over KCs present in training, the documented definition gives −0.241. |
| ASSISTments frequency–position ρ | −0.308 | −0.326 | Not reproducible from the split files under the definition in III.G. The regression file's position column correlates +0.967 with log frequency and is not that proxy. |
| ASSISTments median item support | 44.5 | 32 | 44.5 is the median over KCs with test rows (260). The table now uses KCs present in training for all three datasets. |
| Junyi item support | 18 (IQR 5) | 18 (dense 18) | IQR dropped; median unchanged. |

Junyi (−0.416, −0.324, 18) and XES3G5M (+0.110, −0.126, 3 with dense 9 and sparse 1) reproduce the earlier values exactly under the same definition. E1 (18.9%, 0%, 21.5%) and the test-row counts (415, 17, 4 rows in one partition; 1,969, 114) also reproduce.

## Text

IV.C now cites Tables 6 and 7, gives the recomputed ρ values, and calls XES3G5M "descriptive only". The Introduction's 18.9% and 21.5% now point to Table 7.
