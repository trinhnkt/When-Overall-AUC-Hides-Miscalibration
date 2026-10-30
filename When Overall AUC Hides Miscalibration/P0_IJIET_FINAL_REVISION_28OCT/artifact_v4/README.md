# Artifact v4

Code snapshot: commit 4ff66835561e2597a50197dcfb93aba1ec74583b (2026-10-21 16:03:08 +0700).

The analysis plan in `code/docs/analysis_plan_P0_v2.md` was locked in the parent commit 46e0208 at 2026-10-21 16:02:55 +0700, before the first supplementary training log (2026-10-21 21:58). That plan is the timestamped pre-result plan for the ASSISTments DKT checkpoint-by-window grid and for the masked T-KT correction. Junyi DKT, simpleKT, and fold 5 were added after that plan.

## One command

From this directory:

    py -3 rebuild/reproduce_tables.py

The command does not train. It reads `predictions/` and checks the supported digits in Table 4, Table 5, and Table A2, including the size-matched gaps, the fold-0 intervals, and the rounded counts. It also checks Table A1 (group-level N, AUC, ACC, and the 15-bin Brier decomposition), Tables A3 and A4 (FAR at tau = 0.7) for ASSISTments DKT and T-KT masked, and the G column of Table A5. The supplementary Table A5 intervals are a separate command; see `rebuild/README.txt`.

## Primary protocol

The manuscript's primary protocol has the internal ID P0-BV200-15EW: the validation-AUC checkpoint, non-overlapping test windows of at most 200 responses, and M = 15 equal-width bins, scored on rows with a nonempty test history. The manuscript calls it "the primary protocol".

## What the prediction exports cover

Every included export has folds 0, 1, 2, 3, and 4. Those folds are recomputed from the exports. This artifact is not a fold-0-only package.

| Export | Used for |
| --- | --- |
| ASSISTments DKT, final and best validation, full history and window 200 | Table A2, and the primary row of Tables 4, 5, A1, A3, A4, and A5 |
| ASSISTments T-KT masked, best validation, window 200 | Tables 4, 5, A1, A3, A4, and A5 |
| ASSISTments simpleKT, best validation, window 200 | Table 4 and the sensitivity rows of Table A1 |
| Junyi DKT, best validation, window 200 | post-hoc rows of Tables 4, 5, and A1; the focal group is medium |
| `base_rate_constants.csv` | base-rate rows of Table A1: the constant prediction of each IRT rerun, applied to the DKT rows of the same partition; source hashes and the test-learner check are in the file |

## Other folders

- `statistics/recorded/`: recorded outputs of the 28 Oct revision (Table A1 source metrics, Table A5 run, Tables 6 and 7 descriptors, Table A2 effects, Fig. 3 image). The one command does not read them.
- `scripts_28oct/`: scripts that derived or edited the 28 Oct manuscript text. They need the manuscript or the split files, which are not in this artifact.
- `audits/`: the XES3G5M leakage report (`GATE_B_XES_REPORT.md`) and padding counts (`xes_padding_counts.csv`) cited in Sections III.A and IV.B.

Fold 2 and fold 3 are averaged before the four-partition standard deviation.

## What this artifact does not support

- Retraining. The raw datasets and the model weights are absent.
- Fold 5.
- The slide window.
- XES3G5M. Table 4 already marks it Not evaluated.
- Recomputing Tables 6 and 7. They need the processed split files, which are not shipped.
- Junyi simpleKT.
- Unmasked T-KT.
- Recomputing the published gap from `code/src/ece_uncertainty.py`. That 4ff6683 function keeps a prefix of the concatenated dense rows. The published gap keeps exactly N rows by a second sample without replacement. The command uses `rebuild/published_gap.py`.

## Seeds

`configs/SEEDS.txt`. The YAML files do not list the five scored initialization seeds. The size-match and bootstrap seed is 20261021.

## Logs

`logs/training/` holds the per-run training logs. `logs/A1_DKT_TOKEN0_LOG.txt` is the token-0 check. `logs/UT_A1_A7_TKT_MASKED.txt` is the masked T-KT unit-test run. `tests/` is the test file from commit 4ff6683.
