# A1 — DKT token 0 at commit 4ff6683

Date: 2026-10-29

Source inspected: `src/baseline_runner.py` at commit `4ff66835561e2597a50197dcfb93aba1ec74583b` (2026-10-21 16:03:08 +0700). The DKT class and `collate_fn` are unchanged after that commit. Later edits to `train_torch_model` only add validation logs.

Script: `P0_IJIET_FINAL_REVISION_28OCT/scripts/a1_dkt_token0.py`

Log: `audit/A1_DKT_TOKEN0_LOG.txt`

Manuscript: not edited. No retraining.

## Implementation

Encoding: `token = 2 * KC + y`. Token 0 is a valid interaction: KC 0 with an incorrect response.

| Item | Value at 4ff6683 |
| --- | --- |
| Embedding declaration | `nn.Embedding(n_kcs * 2 + 1, embed_dim, padding_idx=n_kcs * 2)` |
| `padding_idx` | `2 * n_kcs`. Probe with `n_kcs=10` prints 20. Each trained ASSISTments checkpoint has `n_kcs=265`, so `padding_idx=530`. |
| Padding token value passed to the model | `collate_fn` pads features with `padding_value=0`. Labels are padded with `-1`. KC ids are padded with `-1`. |
| Loss mask | `labels_flat != -1`. It does not use `token != 0`. A real token 0 with a label stays in the loss. A padded position is excluded because its label is `-1`. |
| Scoring mask | `predict_windowed` at this commit scores every row whose chunk history is non-empty. It does not drop `token != 0`. The saved chunk files follow that count. |

The reserved embedding row is index `2 * n_kcs`, and that row is exactly zero in every loaded checkpoint. The collate padding value is still 0, so a padded feature looks like token 0. The loss does not train on those padded positions, and an LSTM does not let end-padding change earlier outputs.

## Tests

Comparable-scale rule, fixed before reading the checkpoint norms: `norm(row 0) > 0` and `0.1 <= norm(row 0) / median(norm of the other rows) <= 10`.

| Test | Result |
| --- | --- |
| T0-a `padding_idx is None` or `padding_idx != 0` | PASS. Printed `padding_idx=20` on the probe; trained models use 530. |
| T0-b token 0 at a supervised position has non-zero embedding gradient | PASS. `grad_norm_row0=0.01159726`. One supervised position had token 0. The short row's pad was feature 0 with label `-1` and was outside the mask. |
| T0-c five `best_valid` DKT checkpoints | PASS. Ratios of row 0 to the median of the other rows: fold 0 = 1.022, fold 1 = 1.032, fold 2 = 0.897, fold 3 = 0.943, fold 4 = 1.081. The `padding_idx` row norm is 0. |
| T0-d scored rows and rows after a valid token 0 | PASS. File rows equal test rows on every fold. `no_history` equals the chunk-200 theoretical count. Successors of token 0: 690, 698, 678, 678, 655. None missing. Inside a chunk, `no_history=0` and `p` is finite. Five fold-0 replays from the checkpoint match the saved probabilities within `6.2e-5`. |
| UT-A4 append 20 padding positions | PASS. Appending twenty 0 pads leaves the outputs at the valid positions unchanged (`max abs diff = 0`). |

Checkpoints: `runs/a_dkt/assist2012_fold{0-4}_seed{42,2024,2025,2026,2027}_best_valid/model.pt`.

Predictions: `results/predictions/pred_assist2012_dkt_best_validxchunk_fold{0-4}_{seed}.csv.gz`.

## Decision

**A1 = PASS**

No DKT retraining. Manuscript editing was not started.
