# Gate E — final artifact and submission package

Date: 25/10/2026.

Prerequisite: Gate D is `GATE_D_PASS`. Gate A is `GATE_A_PASS_WITH_SCOPE_REDUCTION`. Gate B is `DESCRIPTIVE_AUDIT_ONLY`. Gate C is `GATE_C_PASS`.

**NOT_READY_TO_SUBMIT**

The package is `P0_IJIET_FINAL_CORRECTION_2026/artifact_final/`. The title uses the hyphen in the Word file, the PDF metadata, the cover letter, and the supplementary note. It was not changed to a colon.

## Checklist

| Item | Result |
| --- | --- |
| Protocol ID locked | Yes. `P0-BV200-15EW`. |
| T-KT valid or excluded | T-KT masked is primary. Unmasked T-KT is excluded. |
| 2×2 complete or causal attribution removed | Complete for ASSISTments DKT. The manuscript does not assign the full-history gap to the checkpoint alone. |
| XES repaired or scope reduced | `DESCRIPTIVE_AUDIT_ONLY`. The manuscript says so. |
| Four-partition summary | Yes. Fold 2 and fold 3 are one partition. |
| Junyi discrepancy | Resolved. −0.0032 is the rounded mean of the per-partition references. |
| Abstract, Table 5, Fig. 3, Conclusion | Consistent. See `audit/GATE_D_CONSISTENCY_REPORT.md`. |
| Artifact rebuilds claimed outputs | Partial. `06_rebuild/README.md` rebuilds Tables 2, 4, 5, 6, A2, and Fig. 3. Table A1, Tables A3–A4, Fig. 1, and Fig. 2 are marked NOT REPRODUCIBLE. |
| Blind manuscript clean | No `FF0000`, no tracked insertions or deletions, empty author metadata, no repository username in the file. Body author line is “Anonymous Authors”. |
| Supplementary | No separate supplementary paper. `07_submission/SUPPLEMENTARY_README.md` says so. |
| Cover letter | Updated. No archived final-checkpoint headline. No three-dataset replication claim. XES is described as audit only. |
| AI statement | The statement is in the manuscript. Every author has not confirmed it in this session. |
| Ethics statement | The statement is in the manuscript. Every author has not confirmed it in this session. |
| References | In the blind file, citations [1] through [31] each have a reference entry, and every entry is cited. The entries were not re-checked against the published sources. |
| PDF | Blind PDF, 12 pages. Title metadata is the hyphenated title. Author metadata is empty. |
| Template | The file downloaded from `https://www.ijiet.org/files/IJIET_template.doc` contains the author copyright and CC BY 4.0 sentence. That sentence was copied. Sample received, revised, and accepted dates were not copied. No DOI, volume, or issue was added. |

## Package

- `00_manifest/`: requirements, git SHA, provenance, prediction checksums, and `claim_to_table_script_prediction.csv`.
- `01_splits/`: train, validation, and test learner ids; seed-to-partition map; temporal splits kept separate.
- `02_training/`: DKT, Junyi, and simpleKT configs; the T-KT masked note; validation logs; checkpoint hashes. Final checkpoints are missing for T-KT masked and Junyi. The primary score uses the validation-AUC checkpoint.
- `03_predictions/`: anonymized rows for ASSISTments DKT, T-KT masked, and Junyi DKT.
- `04_audits/`: gate reports, `LEAKAGE_TEST_LOG.txt` (23 tests passed), and the XES L8 failure.
- `05_statistics/`: ECE, ECE0, ΔECE, ΔECE*, size-match draws, fold-0 bootstrap replicates, binning sensitivity, and support counts.
- `06_rebuild/`: one command, plus the outputs that cannot be rebuilt.
- `07_submission/`: blind Word file, blind PDF, cover letter, AI checklist, ethics checklist, submission checklist, and the template comparison.

## Why this is not ready

Two items are still open.

1. The ethics statement and the AI disclosure have not been confirmed by every author.
2. The reference list matches itself, but it has not been checked against the published sources.

The scientific gates A, B, C, and D are resolved. B is `DESCRIPTIVE_AUDIT_ONLY`, and the manuscript uses that scope. The recorded git commit does not yet contain these Gate D and Gate E edits.
