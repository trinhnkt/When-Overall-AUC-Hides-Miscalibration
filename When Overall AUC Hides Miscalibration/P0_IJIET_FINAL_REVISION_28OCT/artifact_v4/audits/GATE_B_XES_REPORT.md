# Gate B — XES3G5M

Date: 25/10/2026.

Prerequisite: Gate A is `GATE_A_PASS_WITH_SCOPE_REDUCTION`.

Path chosen: **B2**. XES3G5M stays a descriptive audit of distribution, sparsity, and estimability. No event-level retrain was started.

**XES_STATUS = DESCRIPTIVE_AUDIT_ONLY**

## Why this is not model evidence

Three conditions had to pass together: L8 on the route that would be scored, the automated event tests, and a full split audit. They do not.

The runs that exist were scored on the KC-level file. In that file the KC rows of one question attempt stay adjacent, and both training and scoring read earlier rows of the same response before predicting the later KC. For every KC after the first, the outcome of that response is already in the input. L8 fails on that route. Those runs are not reused. No XES AUC or ECE from them is current evidence.

The event-level tests below pass on synthetic sequences. They use `DKTEvent` in `src/xes_events.py` with one question attempt as one step, and they score every KC of a response from history strictly before that response. That class was not trained, and it was not applied to the release. A passing synthetic test does not repair the KC-row runs.

The full question-level audit also fails the split the retrain would need. The released windows are not non-overlapping, and the sequence files do not contain every catalogue question.

## Automated tests

File: `tests/test_xes_events.py`.

Command, from the project root, on 25/10/2026:

`py -3 -m pytest -q tests/test_xes_events.py`

Result: **8 passed** in 1.21s.

| Test | What it checks |
| --- | --- |
| `test_parse_kc_set_counts_a_repeated_kc_once` | A KC repeated inside one concept field counts once. |
| `test_one_label_and_learner_disjoint_and_time_order` | One binary label; train and test learners are disjoint; a later timestamp placed first is rejected. |
| `test_train_frequency_is_train_only_and_once_per_event` | Frequency uses training events only, one count per KC per event. Test events do not count. |
| `test_flip_outcome_leaves_every_kc_probability_unchanged` | For a response with 1 KC, 2 KCs, and 3 KCs, flipping the outcome before feedback leaves every `p(t, c)` in that response unchanged. |
| `test_previous_outcome_can_change_the_next_response` | The same flipped outcome does change the next response. |
| `test_same_question_id_at_a_later_time_is_a_new_event` | The same `question_id` at a later timestamp is a new response. Flipping the first leaves the first probabilities unchanged and moves the later ones. |
| `test_window_concatenation_does_not_repeat_a_response` | Concatenating two non-overlapping windows keeps four distinct response ids. |
| `test_trailing_pad_steps_do_not_change_earlier_predictions` | Extra all-pad steps do not change the probabilities of earlier positions. |

These tests do not read the XES release and do not train.

## Full question-level audit, 25/10/2026

Source files:

- `data/raw/xes3g5m/question_level/train_valid_sequences_quelevel.csv`
- `data/raw/xes3g5m/question_level/test_quelevel.csv`

Padding positions (question id `-1`) are not events. Equal timestamps keep the stored order. Windows of one learner were ordered by the first timestamp in the window. This pass does not use the KC-level file.

| Quantity | Train/valid file | Test file | Both |
| --- | ---: | ---: | ---: |
| Sequence rows | 30,965 | 3,613 | 34,578 |
| Learners | 14,453 | 3,613 | 18,066 |
| Question-attempt events | 4,446,374 | 1,102,810 | 5,549,184 |
| KC attachments | 5,138,603 | 1,274,309 | 6,412,912 |
| Events with more than one KC | 556,877 | 137,777 | 694,654 |
| Distinct questions | 7,618 | 7,052 | 7,651 |
| Learner in more than one fold | 0 | 0 | 0 |
| Learner reappearing after a later learner | 0 | 0 | 0 |
| Timestamp decreases inside a learner | 0 | 0 | 0 |
| Same learner in both files |  |  | 0 |

Question id 6232 is in `metadata/questions.json` and in neither sequence file. The catalogue count 7,652 and the attempt count 7,651 are different counts. No row was added to close the gap. The same 7,651 and the missing id 6232 were recorded on 22/10/2026 in `audit/B4_XES_EVENT_REPORT.md`. The event total 5,549,184 and the attachment total 6,412,912 match that report.

The train/valid file is one learner pool. This audit did not cut it into a separate validation set. A three-way learner-disjoint train/validation/test was not built.

### Window boundary

A response key here is `(learner, timestamp, question_id)`.

| Where the second copy sits | Train/valid | Test |
| --- | ---: | ---: |
| Same window | 45,171 | 11,474 |
| A later window of the same learner | 301 | 0 |

The 301 later-window copies are repeated attempts at the window boundary, not a second estimand to be added to the KC-row flags. One inspected case is learner 2108, fold 0: window 0 ends at position 199 with question 1965, timestamp 1608025529000, response 1, and window 1 starts at position 0 with the same question, timestamp, and response. The 22/10 note that these windows are non-overlapping does not hold for that learner. The full split audit therefore does not pass the no-duplication check.

The 45,171 and 11,474 same-window copies are positions that share a timestamp and a question id with an earlier position in that window. They are not the 301 boundary copies, and they are not the repeat-flag count below.

## Counts that must not be treated as one estimand

| Count | Value | What it counts |
| --- | ---: | --- |
| Question-level interactions in the dataset paper, as cited in the manuscript | 5,549,635 | The paper's question-level total. Not recomputed from these files. |
| Question-attempt events expanded today | 5,549,184 | One event per non-padding sequence position in the two question-level files. |
| KC attachments on those events | 6,412,912 | One attachment per KC on an event. A repeated KC inside one event is kept once by `parse_kc_set`. |
| Valid KC rows in the processed file | 6,413,353 | `manuscript-pack/analysis/xes_padding_counts.csv`, row `valid_nonpadding_rows`. This file is the KC-level route. |
| Repeat flags stated in the manuscript | 863,807 | Second and later KC rows of a multi-KC response, by the release's repeat flags. |
| KC rows minus the paper's question-level total | 863,718 | 6,413,353 − 5,549,635. Arithmetic on two published totals. |
| Attachments minus events | 863,728 | 6,412,912 − 5,549,184. Extra KC attachments after the first KC of an event. |

863,807, 863,718, and 863,728 are not the same quantity. The gap between the repeat-flag count and the arithmetic difference is 89. This audit does not replace any of them.

The processed file also records 7,652 real items and 865 real KCs, including items that have a catalogue entry and no attempt in the question-level sequences. That is why 7,652 and 7,651 can both be true.

## What may still be said

The frequency distribution and the estimability description do not use predicted probabilities. They can stay. Fig. 2 and the estimability text are in that class.

Model-based XES results are excluded. This includes every AUC and ECE from the KC-row runs.

The paper must not claim strong validation across three datasets. ASSISTments 2012 and Junyi Academy are the datasets with model results under the Gate A scope. XES3G5M is not the third model dataset.

## What this gate did not do

- No DKT retrain, no masked T-KT retrain, no simpleKT run.
- No edit to the manuscript, the title, the abstract, or the conclusion. Gate D has to apply this scope when it rewrites the paper.
- Gates C, D, and E were not started.
