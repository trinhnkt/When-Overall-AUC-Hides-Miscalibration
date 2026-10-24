# B2 — DKT on Junyi Academy

Date: 22/10/2026

Protocol: `best_valid × chunk`, patience 8, at most 50 epochs. The contrast is medium minus dense (`100 <= f < 500` versus `f >= 500`). It is not a sparse contrast. Primary rows are `no_history = 0`.

Five runs finished. Fold 2 and fold 3 are one learner partition. `scripts/check_b2_junyi.py` printed `B2_FILES = PASS`. Selected epochs match the first maximum of `valid_auc`.

| fold | init seed | selected epoch | last trained epoch | validation AUC | prediction rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 42 | 4 | 12 | 0.7557 | 3269022 |
| 1 | 2024 | 3 | 11 | 0.7526 | 3243926 |
| 2 | 2025 | 4 | 12 | 0.7546 | 3244494 |
| 3 | 2026 | 4 | 12 | 0.7545 | 3244494 |
| 4 | 2027 | 5 | 13 | 0.7560 | 3163548 |

## Primary contrast

Seed `20261021`. The script was run twice. Both writes of `results/B2_junyi_dkt_uncertainty.csv` were byte-identical (1484 bytes). Both writes of `results/B2_junyi_dkt_secondary.csv` were byte-identical (1425 bytes). Same functions as the ASSISTments A5 table, with the medium group in the role the ASSISTments table gives to sparse. The cluster interval is fold 0 only, B = 2000, R = 200 inside each bootstrap. The point estimate uses R = 2000. Empty medium replicates are `invalid_bootstraps`. Fold 0 had 0.

Source file: `results/B2_junyi_dkt_uncertainty.csv`. Figures below are rounded from that file.

| partition | ECE_medium | ECE_dense | DeltaECE | DeltaECE_star | matched_gap | tail | cluster CI raw | cluster CI matched | N medium | learners | KCs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| fold0 | 0.0291 | 0.0043 | 0.0248 | -0.0038 | 0.0085 | 0.1210 | 0.0177 to 0.0596 | 0.0010 to 0.0434 | 4580 | 169 | 33 |
| fold1 | 0.0262 | 0.0021 | 0.0241 | -0.0096 | 0.0037 | 0.2905 |  |  | 3320 | 150 | 31 |
| fold2 | 0.0382 | 0.0043 | 0.0339 | -0.0095 | 0.0097 | 0.1350 |  |  | 1991 | 123 | 25 |
| fold3 | 0.0446 | 0.0026 | 0.0420 | -0.0014 | 0.0160 | 0.0615 |  |  | 1991 | 123 | 25 |
| fold4 | 0.0413 | 0.0072 | 0.0342 | 0.0063 | 0.0210 | 0.0060 |  |  | 4816 | 142 | 35 |

The script printed the four-partition summary after averaging fold 2 with fold 3: ΔECE 0.030231 (SD 0.006892), ΔECE* −0.003150 (SD 0.006714), matched gap 0.011521 (SD 0.007328), medium ECE 0.034502 (SD 0.008012), dense ECE 0.004271 (SD 0.002144).

ΔECE* is positive only on fold 4. The fold-0 size-matched interval excludes 0. The matched gap is positive on every row. Fold 0 had 0 invalid bootstraps and 2000 used matched replicates.

## Archived pair

`manuscript-pack/analysis/summary_4part_bucket.csv` records the living four-partition pair for Junyi DKT: dense ECE 0.038875 on about 3,226,541 events, medium ECE 0.251340 on about 3,706 events. Those rows are the archived final-checkpoint, full-history protocol. They stay in place. The new medium ECE is about 0.035 and the new dense ECE is about 0.004, so the published pair is not a description of `best_valid × chunk`. The manuscript was not edited in this step.

## Secondary checks

Source: `results/B2_junyi_dkt_secondary.csv`. These do not replace the primary ECE.

On fold 0 the event-level matched gap is 0.0121 (tail 0.003). Equal-width ΔECE at M = 10, 15, and 20 is 0.0185, 0.0248, and 0.0286. Equal-mass ΔECE is 0.0280, 0.0302, and 0.0309. ECE_sweep stops at 10 and 71 bins. Kumar’s debiased squared calibration error is 0.000708 on medium rows and 0.000021 on dense rows.
