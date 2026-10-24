# Data (not included)

Place official dumps here. Git ignores the files and keeps the folder layout.

```
data/raw/assistments2012/
data/raw/junyi/
data/raw/xes3g5m/
data/processed/...
```

Providers:

- ASSISTments 2012: https://sites.google.com/site/assistmentsdata/ — 2012–2013 release with affect.
- Junyi Academy: https://www.kaggle.com/datasets/junyiacademy/learning-activity-public-dataset-by-junyi-academy
  — the Kaggle Online Learning Activity Dataset (logs 2018-08 to 2019-07), **not** Junyi2015 / PSLC DataShop.
  Place `Log_Problem.csv`, `Info_Content.csv`, and `Info_UserData.csv` in `data/raw/junyi/`.
  The pipeline reads `uuid`, `upid`, `ucid`, `timestamp_TW`, `is_correct`; the operational KC is `ucid`.
  Released under CC BY-NC-SA 4.0; cite as Chen, Hsieh, and Tsai (2020).
- XES3G5M: https://github.com/pykt-team/pykt-toolkit
