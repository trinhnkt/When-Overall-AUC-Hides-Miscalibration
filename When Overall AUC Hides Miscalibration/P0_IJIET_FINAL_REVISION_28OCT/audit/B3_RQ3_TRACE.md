# B3 RQ3 from Table A2

Date: 2026-10-29

Status: PASS

Source: Table A2 as printed in the blind manuscript (cells verified against the fold 0-4 prediction exports by artifact v4, `rebuild/reproduce_tables.py`). Script: `scripts/b3_rq3_from_table_a2.py`. Output: `results/B3_TABLE_A2_EFFECTS.csv`.

Effects (ΔECE, ASSISTments DKT):

| Run | best − final, window 200 | best − final, full | 200 − full, final | 200 − full, best |
| --- | --- | --- | --- | --- |
| fold 0 | −0.0774 | −0.0712 | −0.0069 | −0.0131 |
| fold 1 | −0.0716 | −0.0729 | −0.0014 | −0.0001 |
| fold 2 | −0.0217 | −0.0181 | −0.0002 | −0.0038 |
| fold 3 | −0.0381 | −0.0487 | −0.0038 | +0.0068 |
| fold 4 | −0.0527 | −0.0497 | +0.0016 | −0.0014 |

| Check | Computed | Reported | Status |
| --- | --- | --- | --- |
| Checkpoint-associated reduction | 0.0181 to 0.0774 | 0.0181 to 0.0774 | PASS |
| Window-associated change | −0.0131 to +0.0068 | −0.0131 to +0.0068 | PASS |
| Folds 2 and 3 (one learner partition), largest cell difference | 0.0268 in final/full | 0.0268 | PASS |
| Checkpoint direction | best < final in all 10 comparisons | consistent | PASS |

The reported ranges were not changed.

Manuscript changes (named and both blind copies):

- IV.D heading: "D. Sensitivity to checkpoint and test window".
- IV.D paragraph rewritten with the two ranges, the split by window (0.0217 to 0.0774 at window 200; 0.0181 to 0.0729 at full history), the initialization difference 0.0268, "checkpoint-associated difference", and "not a general causal estimate". The words "caused" or "causes" are not used for the checkpoint.
- Section I RQ3 answer rewritten with the verified ranges and the initialization caveat.
- Table A2 numbers unchanged. Abstract not edited in B3.
