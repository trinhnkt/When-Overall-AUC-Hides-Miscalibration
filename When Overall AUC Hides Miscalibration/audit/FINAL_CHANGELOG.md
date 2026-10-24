# Changelog

## 21/10/2026 — A5

- Ran the size-matched dense reference (R = 2000, learners drawn without replacement, then exactly N_sparse events) on all five DKT `best_valid × chunk` runs.
- Ran the learner-cluster bootstrap only on fold 0 (B = 2000, inner R = 200). Empty sparse replicates are counted. Fold 0 had none.
- Wrote `results/A5_uncertainty_dkt_assist.csv`. A second run with seed 20261021 matched the first file byte for byte. The manuscript was not edited.
- R1–R4 were compared with the table. None matches. `audit/A_LEVEL_DECISION.md` records that, and the gate token is `A_GATE_REQUIRES_SUPERVISOR_REVIEW`.

## 22/10/2026 — paper title

- The paper title is `When Overall AUC Hides Miscalibration: Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components`. File names use a hyphen because Windows paths cannot contain a colon. See `audit/NAME_SYNC_2026-10-21.md`.

## 21/10/2026 — names

- An earlier pass pointed the living files at `Reproducible Sparse-Concept and Calibration Diagnostics for Knowledge Tracing`. That is not the current title. The 22/10 entry above replaces it.

## 21/10/2026 — A4

- Recorded the bản I bug at `f5b5d58` line 151: `best_state = model.state_dict()` without `deepcopy`, so the restored checkpoint is the final epoch.
- `select="final"` keeps the last epoch. `select="best_valid"` deepcopies the best validation-AUC epoch, patience 8, maximum 50 epochs.
- UT-C1 trained 5 epochs on a tiny batch, kept an explicit copy per epoch, and checked that the returned weights match the maximum-AUC epoch and differ from the last epoch.
- `scripts/check_a4_checkpoint.py` printed `UT-C1 = PASS` and `A4 = PASS`. It wrote `results/A4_dkt_2x2.csv` from the prediction files. Fold 2 and fold 3 were averaged before the four-partition SD. R1–R4 were not applied.

## 21/10/2026 — A3

- Left `predict_sequential` unchanged. `predict_windowed` already scores `full`, `chunk`, and `slide`, with `no_history = 1` when the window is empty.
- UT-W1 and UT-W2 passed, including the learner count for `full`/`slide` and the chunk count for `chunk`.
- Added `simplekt_no_history` without changing `predict_test`. simpleKT and T-KT-c were not trained.
- Wrote `results/tables/p0_a3_window_context.csv` from the retrained prediction files on disk (folds 0–2). Did not insert 0.0602 or 0.2333. `scripts/check_a3_window.py` printed `A3 = PARTIAL_NOT_RECOVERED`.

## 21/10/2026 — A2

- Did not create a new analysis-plan commit. Commit `46e0208d0fcd3d03d880449e5a6fdd2643619ee0` (21/10/2026 16:02 +07) already locks `docs/analysis_plan_P0_v2.md`, and the first new result file is `train_log.csv` at 21:56.
- `scripts/check_a2_plan.py` printed `A2 = PASS`. Every manifest row cites `analysis_plan_commit` `46e0208`.

## 21/10/2026 — A1

- Confirmed tag `P0-ban-I` and branch `archival/ban-I` at `f5b5d58`. Working branch remains `exp/p0-bo-sung`.
- Rewrote `env.txt` as UTF-8 and added the OS line. Regenerated `requirements-lock.txt` with `pip freeze`.
- Added `scripts/check_a1_freeze.py`. It printed `A1 = PASS`.
- Recorded ban I DKT/T-KT weights as NOT_RECOVERED. Did not copy unrelated checkpoints into the missing slot.
- Recomputed ASSISTments stratum sizes from the split files. Four-partition means are 523971.25, 5963.00, and 415.25. Table 5 rounds these to 523971, 5963, and 415. The new `no_history=0` export on fold 0 is smaller and was left as computed.
