# A3–A5 status

Date: 21/10/2026.

The code for windowed scoring (`src/protocol_v2.py`), checkpoint selection (`select=final` or `select=best_valid` in `src/baseline_runner.py`), and the size-matched interval (`src/ece_uncertainty.py`) is in the tree. Unit tests in `tests/test_protocol_v2.py` cover UT-A1–A7, UT-C1, UT-W1, UT-W2, and the synthetic UT-B checks.

The 2×2 table and the uncertainty table for DKT on ASSISTments were not produced. Ban I checkpoints are NOT RECOVERED, so `full` cannot be re-scored, and `best_valid × chunk` has not been trained. No ECE value was filled in by hand.

R1–R4 are therefore not applied to the manuscript. The DKT cells 0.0602 and 0.2333 stay as the old protocol.
