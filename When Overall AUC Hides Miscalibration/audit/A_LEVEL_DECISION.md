# A-level decision

Date: 21/10/2026

Rules are quoted from `docs/analysis_plan_P0_v2.md`. The manuscript was not edited. R5–R8 are not applied: XES3G5M and T-KT-c were not part of this gate.

## Observed outcome

Primary cell: ASSISTments 2012, DKT, `best_valid × chunk`, `no_history = 0`.

Raw ΔECE is positive on all five runs (0.0846, 0.1016, 0.0867, 0.0935, 0.0808). The size-matched gap is also positive on all five (0.0351, 0.0546, 0.0359, 0.0452, 0.0295). Fold 2 and fold 3 are one partition; both gaps on that partition are positive, and they are not two samples.

On fold 0, the learner-cluster 95% interval for the raw gap is 0.0679 to 0.1323, and for the size-matched gap is 0.0170 to 0.0821. Neither contains 0. Invalid sparse bootstraps: 0.

ΔECE* on the same cell is −0.0088, +0.0074, −0.0118, −0.0050, and −0.0224. After averaging fold 2 with fold 3, three of the four unique partitions have ΔECE* ≤ 0. Only fold 1 is positive.

`final × chunk` and `final × full` from A4 still show a larger raw ΔECE. The contrast is not confined to `final × full`, and it is not absent from `best_valid × chunk`.

Bản I weights are NOT_RECOVERED. The numbers 0.0602 and 0.2333 were not recomputed.

## Matching rule

- R1 does not match. It requires ΔECE* > 0, a positive size-matched gap, and a 95% interval that excludes 0. The interval condition holds on fold 0, and the matched gap is positive, but ΔECE* is not positive on fold 0 or on three of four unique partitions.
- R2 does not match. The size-matched interval on fold 0 excludes 0, so the first clause fails. ΔECE* is not positive while the matched gap is positive, so the second clause fails.
- R3 does not match. The raw contrast is still present under `best_valid` and under `chunk`.
- R4 does not match. The raw contrast is present on every scored protocol in the A4 table.

No pre-specified A-level rule licenses a manuscript rewrite.

## Allowed manuscript conclusion

No new primary sentence is allowed. `docs/claim_evidence.csv` leaves `C-PRIMARY` as UNSUPPORTED until one of R1–R4 applies. None applies. The manuscript stays as it is until the supervisor chooses the wording.

## Claims that must be removed or weakened

- Do not present DKT ECE 0.0602 versus 0.2333 as the result of `best_valid × chunk`. That pair is `C-DKT-OLD`, status CONDITIONAL, and the checkpoint was not recovered. A4’s new `final` runs are a different training.
- Do not say the primary-protocol contrast exceeds the reference bound `0.5 * sqrt(15 / N_sparse)`. On that protocol ΔECE* is negative on fold 0.
- Do not say size matching removes the gap. The matched gap remains positive, and the fold-0 interval excludes 0.
- Do not change the title from this result. R3 is the only rule that even contemplates a title change, its condition is not met, and that rule still requires the supervisor.

## Gate

A3 remains PARTIAL_NOT_RECOVERED. That limitation is recorded and does not by itself fail the gate. A1, A2, and A4 printed PASS. A5 was run twice from seed 20261021 and the files matched. The decision above is recorded. B-level work does not start.

A_GATE_REQUIRES_SUPERVISOR_REVIEW
