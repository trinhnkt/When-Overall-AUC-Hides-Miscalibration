# A5 — Uncertainty for DKT on ASSISTments

Date: 21/10/2026

Executable check: `scripts/check_a5_uncertainty.py`

Registered seed: `20261021`

The script was run twice. Both writes of `results/A5_uncertainty_dkt_assist.csv` were byte-identical (1451 bytes). Both writes of the secondary file were byte-identical (1399 bytes).

Primary data: ASSISTments 2012, DKT, `best_valid × chunk`, rows with `no_history = 0`. Primary ECE is the manuscript 15-bin equal-width function. The uncertainty unit is the learner. There is no event-level bootstrap in the primary interval.

Fold 2 and fold 3 are one learner partition. The table keeps both rows. They are not two inferential samples, and they are not pooled into one interval. The cluster interval is fold 0 only, with B = 2000 and R = 200 size-matched draws inside each bootstrap. The point estimate on every row uses R = 2000. Empty sparse replicates are counted in `invalid_bootstraps`. Fold 0 had 0 empty sparse replicates and 2000 used matched replicates.

## Primary table

Source file, not a hand edit: `results/A5_uncertainty_dkt_assist.csv`. Figures below are rounded from that file. Blank interval cells were not computed.

| partition | ECE_sparse | ECE_dense | DeltaECE | DeltaECE_star | matched_dense_median | matched_gap | matched_tail_probability | cluster CI raw | cluster CI matched | sweep sparse | sweep dense | N sparse | N dense | learners | KCs | B | R | invalid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fold0 | 0.0916 | 0.0070 | 0.0846 | -0.0088 | 0.0564 | 0.0351 | 0.0150 | 0.0679 to 0.1323 | 0.0170 to 0.0821 | 0.0508 | 0.0076 | 430 | 521348 | 155 | 38 | 2000 | 2000 | 0 |
| fold1 | 0.1109 | 0.0094 | 0.1016 | 0.0074 | 0.0564 | 0.0546 | 0.0045 |  |  | 0.0637 | 0.0096 | 423 | 530083 | 140 | 39 | 0 | 2000 | 0 |
| fold2 | 0.0950 | 0.0082 | 0.0867 | -0.0118 | 0.0590 | 0.0359 | 0.0125 |  |  | 0.0749 | 0.0084 | 386 | 514907 | 145 | 37 | 0 | 2000 | 0 |
| fold3 | 0.1036 | 0.0101 | 0.0935 | -0.0050 | 0.0584 | 0.0452 | 0.0040 |  |  | 0.0572 | 0.0103 | 386 | 514907 | 145 | 37 | 0 | 2000 | 0 |
| fold4 | 0.0909 | 0.0101 | 0.0808 | -0.0224 | 0.0613 | 0.0295 | 0.0545 |  |  | 0.0781 | 0.0103 | 352 | 502980 | 153 | 40 | 0 | 2000 | 0 |

`matched_tail_probability` is P(ECE of a size-matched dense draw ≥ ECE_sparse). `DeltaECE_star` subtracts `0.5 * sqrt(15 / N_sparse)`. That term is the bản I reference bound, not a confidence interval.

On fold 0 the raw interval and the size-matched interval both exclude 0. `DeltaECE_star` is negative on fold 0. Sparse support is a few hundred events, about 140 to 155 learners, and about 37 to 40 KCs. No learner-count cutoff is used as a test. The fold-0 interval was estimable: no replicate had an empty sparse group.

## Secondary checks

Source: `results/A5_secondary_dkt_assist.csv`. These do not replace the primary ECE.

Event-level draws of exactly N_sparse dense rows, which ignore learner clusters: fold 0 gap 0.0377 (tail 0.006); fold 1 gap 0.0568 (tail 0.000); fold 2 gap 0.0373 (tail 0.0035); fold 3 gap 0.0453 (tail 0.001); fold 4 gap 0.0300 (tail 0.0255). No draw was invalid.

Equal-width and equal-mass ΔECE at M = 10, 15, and 20 stay positive on every row. M = 15 equal-width remains the primary contrast. On fold 0 the equal-width values are 0.0826, 0.0846, and 0.0915, and the equal-mass values are 0.0808, 0.0816, and 0.0813.

ECE_sweep stops at 5 and 41 equal-mass bins on fold 0 sparse and dense. The sparse sweep value is 0.0508, below the primary sparse ECE of 0.0916. Kumar’s debiased squared calibration error on the same 15 equal-width bins is positive on the sparse rows (fold 0: 0.0041) and near zero on the dense rows (fold 0: 0.00013). The sign of that secondary difference agrees with the primary gap. It is not the estimand.
