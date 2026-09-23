# Reproducible Sparse-Concept and Calibration Diagnostics for Knowledge Tracing

A protocol for Knowledge Tracing on sparse concepts: train-only KC strata, occupancy-aware reporting, ECE/Brier, reliability diagrams, L1–L7 leakage control, and a frozen one-command table rebuild. It is not a new KT architecture and not a classroom trial.

**T-KT** is a local Transformer reference, not published SimpleKT.

This file is written for double-blind review. It does not name authors, a target journal, or a public code URL. Reviewers receive an anonymized code bundle with the manuscript; do not treat this README as a camera-ready citation.

## Manuscript

The submission uses a named file for the editorial office and a separate anonymized file for reviewers. Appendix Tables A1–A6 stay in the main Word/PDF. Do not upload a separate `supplementary.pdf`.

Locked numeric cells are in `sparse-calibration-kt/IJIET_FINAL_REVISION/audit/SCIENTIFIC_LOCKS.md`.

## Datasets

Raw logs are **not** shipped. Obtain them from the original providers and place dumps under `sparse-calibration-kt/data/` (see `sparse-calibration-kt/data/README.md`):

1. [ASSISTments 2012](https://sites.google.com/site/assistmentsdata/) — 2012–2013 release with affect
2. [Junyi Academy Online Learning Activity Dataset](https://www.kaggle.com/datasets/junyiacademy/learning-activity-public-dataset-by-junyi-academy) on Kaggle — **not** Junyi2015 / PSLC DataShop; the operational KC is `ucid`
3. [XES3G5M](https://github.com/pykt-team/pykt-toolkit)

## Reproduce

**LEVEL A** (review-facing): rebuild locked tables from frozen CSVs. No retrain. Does not change ASSISTments T-KT ECE `0.1136` / `0.2280` or FAR `0.196` / `0.268`.

```bash
cd sparse-calibration-kt
pip install -r requirements.txt
bash scripts/rebuild_locked_tables.sh      # Windows: scripts/rebuild_locked_tables.ps1
```

**Track A** retrains local IRT / DKT / T-KT and does **not** recreate those locked cells. See `sparse-calibration-kt/IJIET_FINAL_REVISION/docs/how_to_reproduce.md`.

## Repository layout

| Path | Role |
|------|------|
| `sparse-calibration-kt/src/` | Preprocess, models, metrics, leakage audit |
| `sparse-calibration-kt/scripts/` | LEVEL A rebuild, Track A runners |
| `sparse-calibration-kt/configs/` | Dataset / model YAML |
| `sparse-calibration-kt/results/tables/` | Frozen numeric tables |
| `sparse-calibration-kt/IJIET_FINAL_REVISION/` | Living manuscript sources, figures, frozen analysis |
| `sparse-calibration-kt/tests/` | Unit tests |

## Citation

During review, cite the anonymized accompanying artifact, not a journal article and not a public repository.

```bibtex
@software{sparse_concept_calibration_kt,
  title = {Reproducible Sparse-Concept and Calibration Diagnostics for Knowledge Tracing},
  year  = {2026},
  note  = {Anonymized review artifact}
}
```

A journal name, volume, and DOI should be added only after acceptance.

## License

- Code: [MIT](LICENSE)
- Manuscript text, figures, and appendix tables: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
