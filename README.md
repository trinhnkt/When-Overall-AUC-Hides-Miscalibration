# When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components

A protocol for Knowledge Tracing on sparse concepts: train-only KC strata, occupancy-aware reporting, ECE/Brier, reliability diagrams, L1–L7 leakage control, and a frozen one-command table rebuild. It is not a new KT architecture and not a classroom trial.

**T-KT** is a local Transformer reference, not published SimpleKT.

This file is written for double-blind review. It does not name authors, a target journal, or a public code URL. Reviewers receive an anonymized code bundle with the manuscript; do not treat this README as a camera-ready citation.

## Manuscript

The submission uses a named file for the editorial office and a separate anonymized file for reviewers. Appendix Tables A1–A4 stay in the main Word/PDF. Do not upload a separate `supplementary.pdf`. Validation-AUC checkpoint summaries used in the text are `A4_dkt_2x2.csv`, `A5_*`, `B1_tktc_*`, `B2_junyi_dkt_*`, and `B3_simplekt_*` under `When Overall AUC Hides Miscalibration/results/`. They do not replace the locked Table 5 cells.

Locked numeric cells are in `When Overall AUC Hides Miscalibration/manuscript-pack/audit/SCIENTIFIC_LOCKS.md`.

## Datasets

Raw logs are **not** shipped. Obtain them from the original providers and place dumps under `When Overall AUC Hides Miscalibration/data/` (see `When Overall AUC Hides Miscalibration/data/README.md`):

1. [ASSISTments 2012](https://sites.google.com/site/assistmentsdata/) — 2012–2013 release with affect
2. [Junyi Academy Online Learning Activity Dataset](https://www.kaggle.com/datasets/junyiacademy/learning-activity-public-dataset-by-junyi-academy) on Kaggle — **not** Junyi2015 / PSLC DataShop; the operational KC is `ucid`
3. [XES3G5M](https://github.com/pykt-team/pykt-toolkit)

## Reproduce

**LEVEL A** (review-facing): rebuild locked tables from frozen CSVs. No retrain. Does not change ASSISTments T-KT ECE `0.1136` / `0.2280` or FAR `0.196` / `0.268`.

```bash
cd "When Overall AUC Hides Miscalibration"
pip install -r requirements.txt
bash scripts/rebuild_locked_tables.sh      # Windows: scripts/rebuild_locked_tables.ps1
```

**Track A** retrains local IRT / DKT / T-KT and does **not** recreate those locked cells. See `When Overall AUC Hides Miscalibration/manuscript-pack/docs/how_to_reproduce.md`.

## Repository layout

| Path | Role |
|------|------|
| `When Overall AUC Hides Miscalibration/src/` | Preprocess, models, metrics, leakage audit |
| `When Overall AUC Hides Miscalibration/scripts/` | LEVEL A rebuild, Track A runners |
| `When Overall AUC Hides Miscalibration/configs/` | Dataset / model YAML |
| `When Overall AUC Hides Miscalibration/results/tables/` | Frozen numeric tables |
| `When Overall AUC Hides Miscalibration/manuscript-pack/` | Living manuscript sources, figures, frozen analysis |
| `When Overall AUC Hides Miscalibration/tests/` | Unit tests |

## Citation

During review, cite the anonymized accompanying artifact, not a journal article and not a public repository.

```bibtex
@software{sparse_concept_calibration_kt,
  title = {When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components},
  year  = {2026},
  note  = {Anonymized review artifact}
}
```

A journal name, volume, and DOI should be added only after acceptance.

## License

- Code: [MIT](LICENSE)
- Manuscript text, figures, and appendix tables: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
