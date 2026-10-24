# A2 — Pre-specify the analysis plan

Date: 21/10/2026

Executable check: `scripts/check_a2_plan.py`

```
analysis_plan_commit 46e0208d0fcd3d03d880449e5a6fdd2643619ee0
committed_at 2026-10-21T16:02:55+07:00
first_result train_log.csv
first_result_at 2026-10-21T21:56:20.467255+07:00
timestamp order: plan commit < first result
manifest rows 13 all cite 46e0208
A2 = PASS
```

## What was locked

Commit `46e0208d0fcd3d03d880449e5a6fdd2643619ee0` (“Lock the 21/10 analysis plan before any supplementary run.”) is the only commit that touches `sparse-calibration-kt/docs/analysis_plan_P0_v2.md`. It is 5 hours 53 minutes before the first new result, `runs/a_dkt/assist2012_fold0_seed42_final/train_log.csv`.

The locked plan states:

- Primary estimand: ΔECE = ECE_sparse − ECE_dense for DKT on ASSISTments 2012.
- ECE: 15 equal-width bins, `compute_ece` in `src/calibration_eval.py`.
- Protocol: `best_valid × chunk`.
- Rows: `no_history = 0` only.
- Uncertainty: learner-cluster bootstrap on fold 0 only (B = 2000, R = 200). Not a pooled interval over partitions.
- Description: mean ± SD over four unique learner partitions.
- Secondary: `final` and `best_valid` crossed with `full`, `chunk`, and `slide`; M = 10 and M = 20; equal-mass bins; ECE_sweep; the Kumar et al. (2019) estimator; `no_history` kept with p = 0.5 as sensitivity only.
- Exclusion: drop `no_history = 1`, and report the excluded counts by group and by model.
- Decision rules R1–R8, including XES3G5M (R5–R7) and T-KT-c (R8).

`runs/manifest.csv` records `analysis_plan_commit` as `46e0208` on every row. That prefix is the locking commit. No new plan commit was made after results existed, because that commit would no longer be earlier than the first result.

## Not changed after the runs

The working copy has one extra Deviations sentence saying the A3–A4 queue was started. That sentence is not in commit `46e0208`. It does not change the estimand or R1–R8, and it was not committed.
