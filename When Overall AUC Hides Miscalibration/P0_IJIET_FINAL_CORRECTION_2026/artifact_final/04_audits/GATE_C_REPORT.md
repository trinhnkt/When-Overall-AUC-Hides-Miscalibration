# Gate C — calibration quantities and uncertainty

Date: 25/10/2026.

Prerequisites: Gate A is `GATE_A_PASS_WITH_SCOPE_REDUCTION`. Gate B is `DESCRIPTIVE_AUDIT_ONLY`.

**GATE_C_PASS**

The manuscript was not edited. −0.0032 is the rounded four-partition mean of the per-partition bias references. It is not a hand correction, and it is not `mean(ΔECE) − 0.5·sqrt(15/3706)`.

## Scope

Primary protocol `P0-BV200-15EW`: `best_valid × chunk`, rows with `no_history = 0`, ECE with 15 equal-width bins.

| dataset | model | contrast | role in this gate |
| --- | --- | --- | --- |
| ASSISTments 2012 | DKT | sparse − dense | primary |
| ASSISTments 2012 | T-KT masked | sparse − dense | primary |
| Junyi Academy | DKT | medium − dense | post-hoc; required for the −0.0032 trace |

XES3G5M has no model-based rows. simpleKT stays in `results/B3_simplekt_uncertainty.csv` as a sensitivity table and was not replayed here. Fold 5 is not one of the four partitions.

Fold 2 (init seed 2025) and fold 3 (init seed 2026) are one learner partition, called P2. Their point estimates are averaged first. The four-partition mean and SD then use P0, P1, P2, and P4, with `ddof = 1`. That mean ± SD is descriptive variability. These four partitions are not four independent population samples, and they are not one pooled test.

## Three quantities

They are computed separately. None is a substitute for another.

1. **ΔECE** = ECE of the focal group minus ECE of the dense group. On Junyi the focal group is medium (`100 ≤ f < 500`), not sparse.

2. **ΔECE\*** = ΔECE − 0.5·sqrt(15 / N_focal), with N_focal the focal-group count of that same partition. This is a theoretical bias reference. It is not a confidence interval, not a hypothesis test, not a p-value, and not evidence of significance.

3. **Matched gap** = ECE_focal − median ECE of dense draws of size N_focal. The 95% interval is the learner-cluster bootstrap percentile interval of that gap. It is not ΔECE\*.

On every primary and Junyi row the matched gap is positive. ΔECE\* is negative on some of those same rows. The fold-0 matched interval excludes 0. Those three statements are not the same claim.

## Replay

`scripts/p0_gate_c_export.py` read the prediction files on 25/10/2026. The random stream is seed `20261021`, the same order as `scripts/check_a5_uncertainty.py`: 2,000 learner size-match draws, then 2,000 event-level draws (kept only to preserve the stream), then the fold-0 bootstrap. Replayed ΔECE, ΔECE\*, matched gap, and the fold-0 matched interval match the published uncertainty CSVs within 1e−10. Those published files were not overwritten.

Learner size-match rule, appendix P-6.3:

- permute dense learners without replacement until the concatenated rows reach N_focal;
- if the last learner overshoots, keep exactly N_focal rows by sampling without replacement;
- a draw that cannot reach N_focal is invalid. This replay had 0 invalid draws.

Bootstrap rule, fold 0 only, B = 2,000, inner R = 200:

- unit = learner;
- resample learners with replacement; a repeated learner is a separate cluster;
- recompute ECE_focal, ECE_dense, the inner size-matched dense median, and the matched gap;
- the inner generator is seeded from the parent stream;
- the reported CI95 is the 2.5 and 97.5 percentiles of the 2,000 matched gaps.

Stored files:

- `results/C_partition_detail.csv` — one row per dataset, model, and fold
- `results/C_unique_partition_summary.csv` — one row per unique learner partition
- `results/C_size_match_draws.csv.gz` — 30,000 dense ECE draws (5 folds × 3 models × 2,000)
- `results/C_bootstrap_replicates_fold0.csv.gz` — 6,000 replicates (3 models × 2,000), including empty-replicate columns; this replay had no empty replicate
- `results/C_binning_sensitivity.csv` — M = 10, 15, 20, equal-width and equal-mass
- `audit/JUNYI_DELTAECESTAR_TRACE.csv`

CI95 is filled only for P0. P1, P2, and P4 have no cluster interval because the locked plan computes that interval on fold 0 only. The blank cells are that rule, not a missing file. P2 also has two initialization seeds, so it does not have one interval.

FAR is not used. The column is empty.

## ASSISTments, four unique partitions

Means below are the four-partition mean. The SD is descriptive.

DKT: ECE sparse 0.098172 ± 0.009331, ECE dense 0.008907 ± 0.001338, ΔECE 0.089265 ± 0.009067, ΔECE\* −0.008065 ± 0.012214, matched gap 0.039960 ± 0.010745. Fold-0 matched interval 0.016960 to 0.082110. ΔECE\* is positive only on P1.

T-KT masked: ECE sparse 0.119936 ± 0.024683, ECE dense 0.015823 ± 0.003233, ΔECE 0.104112 ± 0.021516, ΔECE\* 0.006782 ± 0.020703, matched gap 0.058075 ± 0.022980. Fold-0 matched interval 0.023294 to 0.087776. ΔECE\* is negative on P0 and on P2, and positive on P1 and P4.

N_sparse is 430, 423, 386, and 352 on P0, P1, P2, and P4. Both seeds of P2 have that same 386.

## Binning

Primary binning remains 15 equal-width. M = 10, 15, and 20 were scored with equal-width and equal-mass on every fold. All 90 contrasts are positive. There is no negative contrast and no null contrast in this set. No scheme was selected after seeing the test rows.

## Junyi ΔECE\*

Per-fold values are in `audit/JUNYI_DELTAECESTAR_TRACE.csv`, recomputed from the prediction files.

| partition | N_medium | ECE0 | ΔECE | ΔECE\* |
| --- | ---: | ---: | ---: | ---: |
| fold0 | 4580 | 0.028614 | 0.024783 | −0.003831 |
| fold1 | 3320 | 0.033608 | 0.024056 | −0.009553 |
| fold2 | 1991 | 0.043399 | 0.033860 | −0.009539 |
| fold3 | 1991 | 0.043399 | 0.042001 | −0.001398 |
| fold4 | 4816 | 0.027904 | 0.034156 | 0.006251 |

ECE0 = 0.5·sqrt(15 / N_medium) for that fold. ΔECE\* = ΔECE − ECE0.

Aggregation:

1. P2 = the mean of fold 2 and fold 3. For ΔECE\* that mean is −0.005468.
2. The four units are P0 −0.003831, P1 −0.009553, P2 −0.005468, P4 0.006251.
3. Their mean is −0.0031502200. The descriptive SD is 0.006714.
4. Rounded to four decimal places, the mean is **−0.0032**.

The same rounding of the other four-partition means gives ECE medium 0.0345 (from 0.034502), ECE dense 0.0043 (from 0.004271), and ΔECE 0.0302 (from 0.030231). The matched-gap mean is 0.011521.

Applying the bound once to an average N is a different formula:

- 0.030231 − 0.5·sqrt(15 / 3706) = −0.001579
- 0.030231 − 0.5·sqrt(15 / 3676.75) = −0.001705

3706 is the archived final-checkpoint medium count, not a denominator of this protocol. 3676.75 is the mean of the four new unique-partition counts (4580, 3320, 1991, 4816). Neither subtraction is the mean of the per-partition ΔECE\* values. The reported −0.0032 is the per-partition-then-average figure. No `NUMERICAL_DISCREPANCY` flag. The manuscript number was not changed.

## What this gate did not do

- No new interval on P1, P2, or P4.
- No manuscript, title, abstract, or conclusion edit. Gate D still has to keep ΔECE, ΔECE\*, and the matched interval apart when it rewrites the paper.
- Gates D and E were not started.
