From the artifact root:

    py -3 rebuild/reproduce_tables.py

published_gap.py is the random-subset size match and the fold-0 learner-cluster bootstrap.
far_brier.py is FAR at tau = 0.7, its fold-0 KC-clustered bootstrap, and the 15-bin Brier decomposition (Tables A1, A3, A4).
reproduce_tables.py also checks the 16 rows of Table A1 (N, AUC, ACC, Brier, UNC, REL, RES) and the G column of Table A5.
The base-rate rows of Table A1 use predictions/base_rate_constants.csv.

The supplementary Table A5 intervals for folds 1, 2-3, and 4 are a separate command (about 5 minutes each):

    py -3 rebuild/partition_intervals.py points dkt
    py -3 rebuild/partition_intervals.py points tktc
    py -3 rebuild/partition_intervals.py boot dkt 1      (also: dkt 23, dkt 4, tktc 1, tktc 23, tktc 4)
    py -3 rebuild/partition_intervals.py combine

Output: statistics/partition_intervals/C1_PARTITION_INTERVALS.csv. The recorded run is statistics/recorded/C1_PARTITION_INTERVALS.csv.
code/src/ece_uncertainty.py is the 4ff6683 prefix version and is not called by these commands.
