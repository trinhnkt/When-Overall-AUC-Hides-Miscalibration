#!/usr/bin/env python3
"""B1 gate: UT-A1 through UT-A7 must pass before T-KT-c training."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_protocol_v2 import (
    test_ut_a1_past_predictions_ignore_current_label,
    test_ut_a2_future_labels_do_not_change_current_prediction,
    test_ut_a3_prefix_matches_masked_full_chunk,
    test_ut_a4_trailing_pad_does_not_change_valid_positions,
    test_ut_a5_target_of_position_i_is_the_next_row,
    test_ut_a6_short_fit_loss_is_finite_and_falls,
    test_ut_a7_previous_label_changes_the_prediction,
)

TESTS = (
    ("UT-A1", test_ut_a1_past_predictions_ignore_current_label),
    ("UT-A2", test_ut_a2_future_labels_do_not_change_current_prediction),
    ("UT-A3", test_ut_a3_prefix_matches_masked_full_chunk),
    ("UT-A4", test_ut_a4_trailing_pad_does_not_change_valid_positions),
    ("UT-A5", test_ut_a5_target_of_position_i_is_the_next_row),
    ("UT-A6", test_ut_a6_short_fit_loss_is_finite_and_falls),
    ("UT-A7", test_ut_a7_previous_label_changes_the_prediction),
)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    for name, fn in TESTS:
        try:
            fn()
        except Exception as exc:
            print(f"{name} = FAIL")
            print(exc)
            raise SystemExit(1)
        print(f"{name} = PASS")
    print("B1_TESTS = PASS")


if __name__ == "__main__":
    main()
