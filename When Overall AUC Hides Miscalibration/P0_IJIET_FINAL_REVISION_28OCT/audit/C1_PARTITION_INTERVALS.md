# C1 — Multi-partition matched-gap intervals (OPTIONAL)

Status: PASS (run, not skipped). All required prediction exports exist for folds 0–4 of ASSISTments DKT and T-KT masked (best validation, window 200).

Script: `scripts/c1_partition_intervals.py` (modes `points`, `boot`, `combine`). Outputs: `results/C1/points_*.csv`, `results/C1/boot_*.json`, logs in `results/C1/`, and `results/C1_PARTITION_INTERVALS.csv`. The functions are the artifact's `published_gap.py` (A2): size match (R = 2000) and the learner-cluster bootstrap (B = 2000, inner 200). Each supplementary partition uses a generator seeded [20261021, first fold of the partition]; for folds 2–3 the learner draws are shared and G is averaged over the two runs. Fold 0 is the published interval and is unchanged.

| Model | Partition | G | 95% interval | N sparse | Invalid replicates |
| --- | --- | --- | --- | --- | --- |
| DKT | fold 0 (primary) | 0.0351 | 0.0170 to 0.0821 | 430 | 0 |
| DKT | fold 1 | 0.0546 | 0.0331 to 0.1040 | 423 | 0 |
| DKT | folds 2–3 | 0.0406 | 0.0256 to 0.0889 | 386 | 0 |
| DKT | fold 4 | 0.0295 | 0.0089 to 0.0848 | 352 | 0 |
| T-KT masked | fold 0 (primary) | 0.0365 | 0.0233 to 0.0878 | 430 | 0 |
| T-KT masked | fold 1 | 0.0834 | 0.0513 to 0.1439 | 423 | 0 |
| T-KT masked | folds 2–3 | 0.0408 | 0.0286 to 0.0907 | 386 | 0 |
| T-KT masked | fold 4 | 0.0715 | 0.0450 to 0.1251 | 352 | 0 |

Mean ± SD over the four partitions reproduces Table 5: DKT 0.0400 ± 0.0107, T-KT masked 0.0581 ± 0.0230 (B8).

Manuscript: Table A5 (after Table A4); one sentence in the III.E bootstrap paragraph; one sentence in IV.B: "for both models every interval excludes 0, but these supplementary intervals are not combined into one significance claim." The partitions are not independent samples; no pooled test is reported.
