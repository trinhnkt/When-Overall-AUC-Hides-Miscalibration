# A1 — Freeze ban I and standardize prediction export

Date: 21/10/2026

Executable check: `scripts/check_a1_freeze.py`

```
A1 = PASS
```

## Freeze

| Check | Result |
| --- | --- |
| Tag `P0-ban-I` | `f5b5d58cbc5f797e225700debd0177ce49f8bc7c` |
| Branch `archival/ban-I` | same commit; no new commit on this branch |
| Working branch | `exp/p0-bo-sung` |

`scripts/export_predictions.py` is not in `f5b5d58`. It is on the working branch. That is the intended split: ban I stays frozen, export code lives on `exp/p0-bo-sung`.

## Environment

`env.txt` records Python 3.14.4, torch 2.11.0+cu128, CUDA 12.8, pykt-toolkit 0.0.38, NVIDIA GeForce RTX 3090, Windows 10.0.26200.9711.

`requirements-lock.txt` was regenerated with `pip freeze` (157 packages) and written as UTF-8.

## Export schema

`runs/manifest.csv` has the 17 required columns. At the time of the passing check it had 13 rows.

Sample file `results/predictions/pred_assist2012_dkt_best_validxchunk_fold0_42.csv.gz` contains every required prediction column: dataset, split, partition_id, init_seed, model, protocol, run_id, row_index, event_id, user_id, seq_pos, history_len, no_history, item_id, kc_id, f_train, group, y, p.

## Ban I artifacts

ASSISTments DKT weights for ban I: **NOT_RECOVERED**. See `legacy/BAN_I_WEIGHTS.md`. Nothing was invented in their place.

25 other `.pt` files are on disk. They are not ban I DKT or local T-KT.

## Group sizes

Recomputed from the learner-based split files. Fold 2 and fold 3 share one partition and were averaged first. This is the ban I row count, before dropping `no_history`.

| Stratum | Four-partition mean | Manuscript Table 5 | Difference |
| --- | ---: | ---: | ---: |
| dense | 523971.25 | 523971 | +0.25 |
| medium | 5963.00 | 5963 | 0 |
| sparse | 415.25 | 415 | +0.25 |

The manuscript prints the rounded means. The fold-level counts are not equal to those means: dense fold 0 is 528,018; sparse fold 0 is 444.

The new export is a different object. `pred_assist2012_dkt_best_validxchunk_fold0_42.csv.gz` has 534,150 rows and drops 6,763 `no_history` rows. After that drop, fold 0 has dense 521,348, medium 5,598, sparse 430. Those counts are not the Table 5 means, and they were not edited to match Table 5.

## Not claimed

This PASS does not cover A2–A5, and it does not replace any locked ECE cell.
