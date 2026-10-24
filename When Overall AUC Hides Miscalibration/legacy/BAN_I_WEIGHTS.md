# Ban I weights

Status: NOT_RECOVERED

No ASSISTments DKT or local T-KT weight file from ban I is in `results/checkpoints`. The `.pt` files that are on disk are other runs (sparsification, GKT, CL4KT, official SimpleKT). They were not copied here and were not used to fill the missing DKT checkpoint.

The old DKT prediction CSV `results/predictions/assist2012_learner_based_dkt_seed42.csv` is still in place (534,150 rows). It does not use the P-2 column schema. It was left in `results/predictions` rather than duplicated.
