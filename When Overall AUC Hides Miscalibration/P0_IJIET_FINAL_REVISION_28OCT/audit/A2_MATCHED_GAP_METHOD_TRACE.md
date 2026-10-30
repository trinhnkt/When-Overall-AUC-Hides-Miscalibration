# A2 — Size-matched gap and fold-0 learner-cluster interval

Date: 2026-10-29

Decision: **A2 = PASS**.

Section III.E of the named manuscript, the living blind manuscript, and the submission blind manuscript now states the draw, the seed, the stream order, the bootstrap, the empty-replicate rule, and equations (8) and (9). A reader of that section can reimplement G and the fold-0 interval. Table 5 and Table A2 were not edited. The abstract was not edited. No model was retrained.

## Source of 0.0351 and [0.0170, 0.0821]

Those printed values are the fold-0 ASSISTments DKT row of `results/A5_uncertainty_dkt_assist.csv`, written by `scripts/check_a5_uncertainty.py`.

| Quantity | Column | Full value | Printed |
| --- | --- | --- | --- |
| Matched gap | `matched_gap` | 0.035149771608628845 | 0.0351 |
| Interval low | `cluster_CI_matched_low` | 0.01695999586585155 | 0.0170 |
| Interval high | `cluster_CI_matched_high` | 0.08211017574731225 | 0.0821 |

The same script row records `ECE_sparse` = 0.09157636045305016, `matched_dense_median` = 0.05642658884442132, and `matched_gap` = sparse ECE minus that median.

Input file: `results/predictions/pred_assist2012_dkt_best_validxchunk_fold0_42.csv.gz`.

Checkpoint and window: best validation AUC, non-overlapping chunks of 200. Rows kept: `no_history == 0`. Groups: the `group` column, which stores the training-frequency labels. Sparse is `20 ≤ ftrain < 100`. Dense is `ftrain ≥ 500`.

## Code

| Step | File | Function |
| --- | --- | --- |
| Point estimate and bootstrap call | `scripts/check_a5_uncertainty.py` | `one_partition` |
| Learner alignment | `scripts/p0_a5_dkt_assist.py` | `aligned_users` |
| Event-level draw that only advances the stream | `scripts/p0_a5_dkt_assist.py` | `row_matched` |
| Dense draw and gap | `src/ece_uncertainty.py` | `dense_at_n`, `size_matched_contrast` |
| Bootstrap | `src/ece_uncertainty.py` | `cluster_bootstrap_diff` |
| 15-bin ECE | `src/calibration_eval.py` | `compute_ece` |

`scripts/p0_gate_c_export.py` replays this stream. It was not a second definition.

## Parameters taken from the code

| Parameter | Value |
| --- | --- |
| Random seed | 20261021, one `numpy.random.Generator` |
| Fold order | 0, then 1, 2, 3, 4. Fold 0 starts at the seed. |
| Point-estimate draws R | 2000 |
| Bootstrap replicates B | 2000, fold 0 only |
| Inner draws per replicate | 200 |
| Percentiles | 2.5 and 97.5, NumPy linear |
| ECE bins | 15 equal-width |
| Invalid point-estimate draws on fold 0 | 0 (`matched_draws_invalid`) |
| Empty sparse bootstrap replicates | 0 (`n_empty_sparse`, stored as `invalid_bootstraps`) |
| Other invalid bootstrap replicates | 0 (`n_empty_or_invalid`, stored as `bootstrap_excluded`) |
| Replicates inside the interval | 2000 (`bootstrap_matched_used`) |

## The six draw steps

The implementation matches the requested construction.

1. Dense learners with at least one dense row are permuted without replacement (`Generator.permutation`).
2. Their dense rows are appended until the concatenated length is at least `N_sparse`.
3. Exactly `N_sparse` of those rows are retained by `Generator.choice(..., replace=False)`. The last learner may cross `N_sparse` and then lose some of its rows.
4. This is repeated R = 2000 times.
5. The dense reference is the median of the valid dense ECE values.
6. G is sparse ECE minus that median (`size_matched_diff`).

A draw with fewer than `N_sparse` dense rows returns no sample and is omitted from the median. Fold 0 had no such draw.

Learners are ordered by first appearance in the prediction file among rows with `no_history == 0`.

## What matching does

Matching equalizes the number of rows only. It does not equalize ECE bin occupancy, the predicted-probability distribution, or the dependence structure.

## Fold-0 interval

The parent generator is used in three stages. Stage 1 is the R = 2000 draws in G. Stage 2 is `row_matched`: 2000 calls of `choice` with `replace=False` on the pooled dense rows in prediction-file order. Stage 2 is not part of G and is not part of the interval. Replaying the published interval still has to run stage 2, because those calls move the generator. Stage 3 is `cluster_bootstrap_diff`.

Each bootstrap replicate draws learner indices with `Generator.integers(0, n_learners, size=n_learners)`. The population is every test learner with a nonempty history, including learners who have an empty sparse side or an empty dense side. A repeated index is stored as a separate cluster, and its rows are concatenated again.

A replicate with no sparse rows is counted in `n_empty_sparse`, stored as missing, and left out of the percentiles. Its gap is not imputed. A replicate with no dense rows, or a replicate whose inner size-matched gap is missing, is counted in `n_empty_or_invalid` and left out in the same way. Fold 0 had 0 of each, so all 2000 replicates enter the percentiles.

For each valid replicate the parent generator draws one integer on `[0, 2^31 - 1)` and that integer seeds the inner generator. The inner generator repeats the size-matched draw 200 times.

## ECE bins

`compute_ece` places edges at `linspace(0, 1, 16)`. The first bin contains predicted probabilities on `[0, 1/15]`. Each later bin contains probabilities on `(left, right]`.

## Equation numbers

Equations (1)–(7) were already in the manuscript, and the FAR display was (8). Section III.E now has:

- (8) ECE of the rows retained on draw r
- (9) G = ECE_sparse − median over r of that dense ECE

FAR was renumbered from (8) to (10). No other equation label was changed.

## Files edited

- `manuscript-pack/manuscript/When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components.docx`
- the living `_blind.docx` in the same folder
- `P0_IJIET_FINAL_CORRECTION_2026/artifact_final/07_submission/…_blind.docx`

The PDF and the `.doc` exports were not regenerated.
