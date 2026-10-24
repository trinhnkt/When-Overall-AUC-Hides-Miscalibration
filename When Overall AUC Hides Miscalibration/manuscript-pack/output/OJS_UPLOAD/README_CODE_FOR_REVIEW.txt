Anonymous code bundle for IJIET double-blind review
Packed: 24 October 2026 (104 files)

This zip is the reviewer-facing LEVEL A artifact. It does not contain:
- author names, emails, affiliations, or a public GitHub URL
- named or blind Word/PDF manuscript sources
- supplementary.pdf or former S1–S10 TeX sources (printed tables are
  Tables 1–6 and Appendix A1–A4 in the manuscript)
- GKT / CL4KT code (not scored in the paper)
- Word layout helpers, raw logs, checkpoints, or prediction dumps

It contains local IRT / DKT / T-KT evaluation code, frozen table CSVs
used by the 12-page manuscript, masked XES3G5M a2b summaries,
and a2b Python (no processed logs). Obtain public benchmarks from the
original providers (ASSISTments 2012, Junyi Academy, XES3G5M).

T-KT is a local Transformer reference used to stress-test the diagnostic
protocol. It is not published SimpleKT.

Rebuild reported tables from frozen summaries (does not retrain):
  scripts/rebuild_locked_tables.sh
  scripts/rebuild_locked_tables.ps1

Locked ASSISTments T-KT cells: ECE 0.1136 / 0.2280; FAR 0.196 / 0.268.
Table 5 DKT cells 0.0602 / 0.2333 are unchanged.

results/validation_checkpoint/ holds the summaries behind the
validation-AUC sentences in the text. Those files are not prediction
dumps and do not replace Table 5.
  A4_dkt_2x2.csv
  A5_uncertainty_dkt_assist.csv
  A5_secondary_dkt_assist.csv
  B1_tktc_uncertainty.csv
  B1_tktc_secondary.csv
  B2_junyi_dkt_uncertainty.csv
  B2_junyi_dkt_secondary.csv
  B3_simplekt_uncertainty.csv
  B3_simplekt_secondary.csv
