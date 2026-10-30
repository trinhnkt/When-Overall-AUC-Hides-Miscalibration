# B1 — Abstract rewritten last

Status: PASS. Script: `scripts/b1_abstract.py` (`--write` applied to the three copies; `--check` re-verifies the saved files).

Prerequisites at the time of the rewrite: A1, A2, A3, A4, A5 PASS; B3, B5, B6 done; B8 covered by Table A5 and `results/C1_PARTITION_INTERVALS.csv`. Only the text after the "Abstract—" run was replaced; that run keeps its formatting (`fmt_check.py`: no new losses). The new body is red for review.

## Text (197 words)

Knowledge tracing (KT) models are usually ranked by the area under the receiver operating characteristic curve (AUC) over all responses, which can hide poor calibration on knowledge components (KCs) that learners rarely practice. We fix one protocol on ASSISTments 2012: the validation-AUC checkpoint, non-overlapping test windows of at most 200 responses, 15 equal-width bins, training-count frequency groups, and four unique learner partitions. For deep knowledge tracing (DKT), the mean expected calibration error (ECE) was 0.0982 on sparse KCs and 0.0089 on dense KCs, a difference of 0.0893. When dense rows were subsampled to the sparse sample size, the gap was 0.0400, and its learner-cluster 95% interval on one partition was 0.0170 to 0.0821. A causally masked Transformer showed the same direction, with a difference of 0.1041. In a checkpoint-by-window grid for DKT, the validation-AUC checkpoint was associated with a sparse–dense difference lower by 0.0181 to 0.0774 than the final checkpoint, whereas changing the test window shifted it by −0.0131 to +0.0068. The evidence comes from one dataset with a mean of 398 sparse responses per partition, and Junyi Academy had no sparse group. Reports should give frequency-stratified calibration, group sizes, and the checkpoint rule alongside overall AUC.

## Structure

| Required part | Sentence |
| --- | --- |
| Problem | 1 |
| Protocol | 2 |
| Primary quantitative result | 3–5 |
| 2×2 result | 6 |
| Scope limitation + recommendation | 7 (one sentence), 8 |

## Number trace

| Value | Source |
| --- | --- |
| 0.0982, 0.0089, 0.0893 | Table 5, ASSISTments DKT sparse ECE, dense ECE, ΔECE |
| 0.0400 | Table 5, DKT matched gap G |
| 0.0170 to 0.0821 | Table 5, 95% CI column (fold-0 learner-cluster interval of G) |
| 0.1041 | Table 5, T-KT masked ΔECE |
| 398 | Table 5, ASSISTments sparse N (mean count, rounded) |
| 0.0181 to 0.0774 | Table A2 via `results/B3_TABLE_A2_EFFECTS.csv`, best_valid − final, min and max magnitude over both windows and five runs |
| −0.0131 to +0.0068 | Table A2 via the same CSV, window200 − full at both checkpoints |
| 2012, 200, 15, 95, four | protocol settings, not results |

The checker extracts every number in the Abstract and fails if it is not a protocol setting or a value in Table 5 or the Table A2 effects file.

## Checks (all three copies)

- Word count 197 (target 180–200): PASS.
- KT, KC, AUC, ECE, DKT defined at first use: PASS.
- No "fold-0", "fold 0", "ΔECE"/"DeltaECE", "P0-BV200", or audit wording: PASS. "One partition" replaces "fold 0"; ΔECE* is not mentioned.
- Model claim follows B6: "showed the same direction"; no claim that presence depends on the model.
- Wording follows B3: "was associated with", not "caused".

Removed from the old Abstract: the ΔECE* values, the XES3G5M leakage sentence, the "unmasked Transformer excluded" sentence, the SD disclaimer, and the "size and presence depend on … the model" sentence. These remain in the body where the evidence is given.
