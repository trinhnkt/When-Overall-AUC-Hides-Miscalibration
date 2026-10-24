# C2 — positional-embedding ablation on T-KT-c

Date: 22/10/2026

`TKTPE` adds a learned positional embedding of length 200 on top of T-KT-c. The class is in `src/protocol_v2.py`. `TKTc.forward` is unchanged. This is an ablation on ASSISTments fold 0, init seed 42, `best_valid × chunk`. It is not a replacement model and it does not replace the five-run T-KT-c table.

## Training

`scripts/p0_c2_tktpe.py` wrote `results/predictions/pred_assist2012_tkt_pe_best_validxchunk_fold0_42.csv.gz` (534150 rows). Device: CUDA. Patience 8, at most 50 epochs. The train log is `runs/c2_tktpe/assist2012_fold0_seed42_best_valid/train_log.csv`. Epoch numbers in that log start at 0.

`scripts/check_c2_tktpe.py` printed `C2_FILES = PASS`. The selected epoch in `runs/manifest.csv` is 7, the first maximum of `valid_auc` (0.722248). The last trained epoch is 15. Three early log lines round to 0.7222; the unrounded maximum is epoch 7.

## Comparison

Same test file as T-KT-c fold 0 seed 42. Rows `no_history = 0`. Both files drop 6763 empty-window rows. Group counts match. ECE uses 15 equal-width bins. Figures are rounded from the script print. Full values are in `results/C2_tktpe_vs_tktc_fold0.csv`.

| model | group | N | AUC | ECE |
| --- | --- | ---: | ---: | ---: |
| TKT_PE | sparse | 430 | 0.7649 | 0.0954 |
| TKT_PE | dense | 521348 | 0.7176 | 0.0152 |
| T-KT-c | sparse | 430 | 0.7857 | 0.0951 |
| T-KT-c | dense | 521348 | 0.7226 | 0.0120 |

| model | overall AUC | DeltaECE | DeltaECE* |
| --- | ---: | ---: | ---: |
| TKT_PE | 0.7192 | 0.0803 | -0.0131 |
| T-KT-c | 0.7242 | 0.0832 | -0.0102 |

Strict cold start has 0 events on this fold. Very sparse has 11 events. Those two groups are too small for a contrast.

On this one run the positional embedding lowers overall AUC by about 0.005 and lowers sparse AUC from 0.786 to 0.765. Sparse ECE stays at 0.095. Dense ECE moves from 0.0120 to 0.0152. ΔECE* stays negative for both models. The T-KT-c row matches the fold-0 row already stored in `results/B1_tktc_uncertainty.csv`. The manuscript was not edited.
