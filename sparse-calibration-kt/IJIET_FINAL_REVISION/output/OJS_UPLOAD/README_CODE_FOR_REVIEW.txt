Anonymous code bundle for IJIET double-blind review
Packed: 23 September 2026 (95 files)

This zip is the reviewer-facing LEVEL A artifact. It does not contain:
- author names, emails, affiliations, or a public GitHub URL
- named or blind Word/PDF manuscript sources
- supplementary.pdf or former S1–S10 TeX sources (those tables are
  Appendix A1–A6 in the manuscript)
- GKT / CL4KT code (not scored in the paper)
- Word layout helpers, raw logs, checkpoints, or prediction dumps

It contains local IRT / DKT / T-KT evaluation code, frozen table CSVs
used by the living 13-page manuscript, masked XES3G5M a2b summaries,
and a2b Python (no processed logs). Obtain public benchmarks from the
original providers (ASSISTments 2012, Junyi Academy, XES3G5M).

T-KT is a local Transformer reference used to stress-test the diagnostic
protocol. It is not published SimpleKT.

Rebuild reported tables from frozen summaries (does not retrain):
  scripts/rebuild_locked_tables.sh
  scripts/rebuild_locked_tables.ps1

Locked ASSISTments T-KT cells: ECE 0.1136 / 0.2280; FAR 0.196 / 0.268.
