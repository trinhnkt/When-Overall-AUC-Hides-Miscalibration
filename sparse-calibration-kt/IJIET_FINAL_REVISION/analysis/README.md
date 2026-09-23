# Analysis copies (not new experiments)

Locked artifacts in this folder. Do not edit numbers here and then treat them as a new run.

| File | Role |
|------|------|
| `summary_4part_bucket.csv` | Four-partition ECE/Brier (ASSISTments, Junyi) |
| `four_partition_punchline_ece.csv` | Punchline ECE copy |
| `c2_fivefold_verdict.txt` | Locked ASSISTments seed-42 CI [0.006, 0.138] |
| `ijiet08_*.csv` | Frozen Assist gate recoveries |

## XES3G5M source of truth (A2B, padding excluded)

Do not re-derive manuscript XES ECE/FAR/Miss from `c2_fivefold_verdict.txt` or from unmasked four-partition CSVs. Use `a2b/analysis/` (`c2_xes_verdict.txt`, `summary_4part_*.csv`, `a9/statistical_summary.csv`). ASSISTments locked CI in `c2_fivefold_verdict.txt` is unchanged.
