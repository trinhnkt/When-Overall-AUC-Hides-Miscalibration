# B2 — Notation standardization

Status: PASS for the manuscripts. The protocol-ID line in the artifact README is written by the artifact v4 rebuild (see REVISION_STATUS, item ART).

Scripts: `scripts/b2_notation.py` (text and tables; `--check` is the blind-file checker), `scripts/b2_fig3.py` (Fig. 3 image).
Applied to all three copies in `msedit.PATHS` (named, living blind, submission blind). Changed runs are red for supervisor review.

## Definition

III.C ("Table 2 lists the runs…") now has the only definition:

> We call this setting the primary protocol (internal ID P0-BV200-15EW): the validation-AUC checkpoint, non-overlapping test windows of at most 200 responses, and M = 15 equal-width bins (Section III.E).

## Replacements

| Location | Before | After |
| --- | --- | --- |
| Section I, RQ paragraph | under protocol P0-BV200-15EW, | under the primary protocol (Section III.C), |
| Table 2 caption | under P0-BV200-15EW | under the primary protocol |
| Table 4 caption | Protocol P0-BV200-15EW. / N is that mean count. | All rows use the primary protocol. / N is the mean count, rounded. |
| Table 4 | Protocol ID column | removed (5 columns) |
| Table 4 N | 523611.5, 3204343.0 | 523,612, 3,204,343 |
| IV.B first paragraph | under protocol P0-BV200-15EW | under the primary protocol |
| IV.B | ΔECE* is positive only on P1 | … only on fold 1 |
| IV.B | positive on P1 and P4 and negative on P0 and P2 | positive on fold 1 and fold 4 and negative on fold 0 and folds 2–3 |
| IV.B Junyi paragraph | mean N medium = 3676.75 | mean count N medium = 3,677 |
| Table 5 caption / N | N is the mean count; 397.75, 517329.5, 3676.75, 3200666.3 | N is the mean count, rounded; 398, 517,330, 3,677, 3,200,666 |
| Table A2 N sparse | 430.0000, 423.0000, 386.0000, 386.0000, 352.0000 | 430, 423, 386, 386, 352 |
| Table A3 caption | under protocol P0-BV200-15EW | under the primary protocol |
| Table A4 caption / N, Nadv, Ninc | sparse-group means; 397.75 / 190.63 / 191.88 / 156.50 | sparse-group mean counts, rounded; 398 / 191 / 192 / 157 |
| Fig. 3 image title | ASSISTments 2012, protocol P0-BV200-15EW, fold 0 only | ASSISTments 2012, primary protocol, fold 0 |

Rounding is half-up from the unrounded means (`msedit.count`). No metric value changed.

## Fig. 3

`p0_gate_d_rebuild.py` was not re-run. `b2_fig3.py` copies its `write_fig3` plot code, changes only the title and the thousands separator in the legend, and asserts N and ECE per panel against the printed values (DKT sparse 430 / 0.0916, dense 521,348 / 0.0070; T-KT masked sparse 430 / 0.0951, dense 521,348 / 0.0120). Output `results/fig3_primary_protocol_fold0.png` (sha256 1a8e1206…d770, 1440×660 px, same size as the old image), swapped into `word/media/image3.png` of all three copies after checking the old image hash db13b34afa33.

## Blind-file checker (`py -3 scripts/b2_notation.py --check`)

| Check | Named | Living blind | Submission blind |
| --- | --- | --- | --- |
| P0-BV200 occurrences ≤ 1 | PASS (1) | PASS (1) | PASS (1) |
| No standalone P0–P5 partition labels | PASS | PASS | PASS |
| No count ending .0000 (integer part ≥ 1) | PASS | PASS | PASS |
| No fractional mean counts | PASS | PASS | PASS |

Metric values of 0.0000 (for example REL of a dense group) are not counts and are not flagged.

Other checks after B2: `table6_context.py --check` prints "All values match"; `fmt_check.py` reports only the known A3 paragraph ("Two secondary analyses…").

## Follow-up (`scripts/b2_notation_followup.py`)

| Location | Before | After |
| --- | --- | --- |
| RQ1 | Under the locked protocol, | Under the primary protocol, |
| IV.D (Table A2 paragraph) | cut points were not evaluated under this protocol | … under the primary protocol |
| Conclusion | under the locked validation-AUC and window-200 protocol, | under the primary protocol, |
| V.D Limitations (C1) | The matched interval covers fold 0 only. | The primary matched interval covers fold 0 only; the Table A5 intervals for the other partitions are supplementary. |

After the follow-up: "locked protocol", "window-200 protocol", and "under this protocol" occur 0 times; "primary protocol" occurs 19 times in each copy. The blind-file checker still passes.

## Artifact README

`artifact_v4/README.md` (rebuilt 2026-10-29 by `scripts/a5_build_artifact.py`) contains P0-BV200-15EW exactly once, in the "Primary protocol" section.

Not done here: the PDF and .doc copies were not regenerated.
