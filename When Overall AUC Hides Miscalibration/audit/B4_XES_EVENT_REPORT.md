# B4 — XES3G5M question-level events

Date: 22/10/2026

Source files: `data/raw/xes3g5m/question_level/train_valid_sequences_quelevel.csv` and `test_quelevel.csv`. The kc_level files were not used. A learner with a long history is stored as several non-overlapping windows of 200. Padding positions have question id `-1` and are not events. Equal timestamps keep the original order inside a window, then the window order.

## Sample of 1,000 learners

`scripts/check_b4_utb.py sample` printed `UT-B1 = PASS` through `UT-B8 = PASS` and `B4_SAMPLE = PASS`. The sample contains 6,125 distinct questions, 327,998 events, and 376,393 KC attachments. The 7,652 check is not applied to the sample.

## Full release

The same script in `full` mode printed `UT-B1 = PASS` through `UT-B7 = PASS`. The event table has 5,549,184 events, of which 694,654 have more than one KC, and 6,412,912 KC attachments.

`UT-B8` did not pass. The sequences contain 7,651 distinct questions. `data/raw/xes3g5m/metadata/questions.json` lists 7,652. The missing id is 6232. It has a catalogue entry and no question attempt, so it is not an event. No row was added to make the count equal 7,652.

## Decision

Rule R7 applies. XES3G5M is not trained in this round. DKT-event and T-KT-c-event were not started. The living XES treatment stays as it is. No new XES ECE is reported.
