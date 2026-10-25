# Protocol decision log

Date: 25/10/2026.

Primary protocol ID: P0-BV200-15EW.

Definition: learner-disjoint train/validation/test; checkpoint = maximum validation AUC (est_valid, patience 8, at most 50 epochs); test context = non-overlapping windows of at most 200 (chunk); KC frequency from training rows only, cuts 0 / 20 / 100 / 500; ECE = 15 equal-width bins on rows 
o_history = 0, function compute_ece. Fold 2 (init seed 2025) and fold 3 (init seed 2026) are one learner partition. They are not two inferential samples.

inal + full history is not this protocol. Retrained inal × full and inal × chunk rows below are SENSITIVITY. The published bản I pairs (DKT 0.0602/0.2333, unmasked T-KT 0.1136/0.2280, simpleKT 0.0203/0.0884, Junyi DKT 0.0389/0.2513, Junyi T-KT 0.0817/0.1136) have no recovered prediction file. They are LEGACY. Unmasked T-KT is INVALID for a main claim.

## What may be called pre-specified

Commit 46e0208d0fcd3d03d880449e5a6fdd2643619ee0 (2026-10-21 16:02:55 +0700) locks docs/analysis_plan_P0_v2.md before the first supplementary train log (21:56 the same day). That commit names:

- the primary DKT estimand on ASSISTments 2012 under est_valid × chunk
- the secondary grid of inal/est_valid by ull/chunk/slide
- the decision, before any T-KT-c training, to replace unmasked T-KT with T-KT-c

Those rows are marked pre-specified in 46e0208.

Junyi DKT, the simpleKT reruns, fold 5, the positional ablation, and Junyi simpleKT were not in that commit. They are post-hoc robustness analysis. Do not call them pre-specified.

## Freeze

- Code SHA on every scored run: 4ff6683. Plan SHA: 46e0208.
- Configs: configs/assist2012.yaml, configs/junyi.yaml. Fold 5 uses scripts/create_new_folds.py (shuffle seed 2028).
- Libraries in 
equirements-lock.txt: torch 2.11.0+cu128, numpy 2.4.3, pandas 2.3.3, scikit-learn 1.8.0. pyKT is the local tree 	hird_party/pykt-toolkit, not a PyPI pin.
- Prediction checksums: on 25/10/2026, SHA-256 of all 54 prediction files in 
uns/manifest.csv matched the manifest. No mismatch.
- Data: processed learner-based splits under data/processed/. No separate dataset-release checksum is stored in the manifest.
- Bản I checkpoints: NOT_RECOVERED.

## Records with no prediction file

| dataset | model | ckpt rule | history rule | mask rule | role | note |
| --- | --- | --- | --- | --- | --- | --- |
| assist2012 | T-KT unmasked | final | full | no causal mask | INVALID | Table 5 pair 0.1136 / 0.2280. Not a second model. |
| junyi | T-KT unmasked | final | full | no causal mask | INVALID | 0.0817 to 0.1136. Masked retraining was not run. |
| assist2012 | DKT bản I | final | full | lstm_shift_pad0 | LEGACY | 0.0602 / 0.2333. Weights not recovered. |
| junyi | DKT bản I | final | full | lstm_shift_pad0 | LEGACY | 0.0389 / 0.2513. Weights not recovered. |
| assist2012 | simpleKT bản I | final | full | not archived | LEGACY | 0.0203 / 0.0884. No archived train log. |
| xes3g5m | any model |  |  |  | DESCRIPTIVE_AUDIT_ONLY | L8 failed on the KC-row route. Gate B, 25/10/2026, path B2. No AUC or ECE. See audit/GATE_B_XES_REPORT.md. |

## Experiment keys

Canonical key: (dataset, fold, seed, model, code_sha, ckpt_rule, history_rule, mask_rule).

KC groups for every row: training-count only. Metric configuration for every row: 15 equal-width ECE, 
o_history = 0.

| dataset | fold | init seed | model | code SHA | ckpt rule | history rule | mask rule | KC groups | metrics | prediction file | sha256 | role | timing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| assist2012 | fold0 | 42 | dkt | 4ff6683 | final | full | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxfull_fold0_42.csv.gz | 4048c4766833b806dc1a6d9838f44ba61febf7dbbe91895222d670b5afd91a56 | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold0 | 42 | dkt | 4ff6683 | final | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxchunk_fold0_42.csv.gz | 9d7ea323a11ce53f11db9eaa84e7422771c72578d87b6a3ab0d281a2610c5e0e | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold0 | 42 | dkt | 4ff6683 | final | slide_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxslide_fold0_42.csv.gz | e9eb967a9ac08806ec8b74f0562eee3aa90d6c654e80c8e1101a65133723e11f | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold0 | 42 | dkt | 4ff6683 | best_valid | full | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxfull_fold0_42.csv.gz | a1645220c3cb7277b00e4b0b4f710025338a5b23e35168ae3500db55c45c7fef | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold0 | 42 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxchunk_fold0_42.csv.gz | be37c80b30185c9a7af4f3d8412917c18913b7acb2342678b686825762362efa | PRIMARY | pre-specified in 46e0208 |
| assist2012 | fold0 | 42 | dkt | 4ff6683 | best_valid | slide_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxslide_fold0_42.csv.gz | 969caad0364c69e8b26e9fc571216fa805412ba7fc298fc655b114df898c467c | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold1 | 2024 | dkt | 4ff6683 | final | full | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxfull_fold1_2024.csv.gz | 5e3ce0b755454b271e4cf50f4f52ab7ad170ad4b1820b8212d0e533f58908a4f | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold1 | 2024 | dkt | 4ff6683 | final | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxchunk_fold1_2024.csv.gz | 82c0bdac8338d0ba10ccb0e0fbfcd5cbd5bbf040bdc5a8a8e48b716781ab7970 | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold1 | 2024 | dkt | 4ff6683 | final | slide_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxslide_fold1_2024.csv.gz | fdb42f75356ac9a80ac9ebad4f4d25c79c373706bf0b0433b725eb1a3f0206be | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold1 | 2024 | dkt | 4ff6683 | best_valid | full | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxfull_fold1_2024.csv.gz | 77d0ff309c2147d69759aff60eb2130581342ef2f99a7496c1d8660a3848e04c | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold1 | 2024 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxchunk_fold1_2024.csv.gz | 7d2b95fb7b3360b973586e2ea6c84a23139505adafab8517b1d67ca63a5d74f9 | PRIMARY | pre-specified in 46e0208 |
| assist2012 | fold1 | 2024 | dkt | 4ff6683 | best_valid | slide_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxslide_fold1_2024.csv.gz | 6c814688eca3e6e921f5482d44050091e8a60f9742ba1178a95b2268904384b1 | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold2 | 2025 | dkt | 4ff6683 | final | full | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxfull_fold2_2025.csv.gz | 9b8e3bee73b27b6b24337b8f6fe83926dffe3c83f07def0ebb4d304a7c7e66d3 | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold2 | 2025 | dkt | 4ff6683 | final | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxchunk_fold2_2025.csv.gz | 7f80ad7f3221996a0c1f7f8dedce15b2c23934dc28ff25e8f1c4f7d4f53768e4 | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold2 | 2025 | dkt | 4ff6683 | final | slide_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxslide_fold2_2025.csv.gz | 5114b36c66d0d4b55683e393609c5590795d26b0978178ef973bfdaa6749767c | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold2 | 2025 | dkt | 4ff6683 | best_valid | full | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxfull_fold2_2025.csv.gz | 5c967391896f9f1840ddf34e5a54ba325dbed263a57d07e6bab2802debea334f | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold2 | 2025 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxchunk_fold2_2025.csv.gz | 27a74d993730cf4afb85cbb7b87e9494a3cfa60cd650e0af8f9a3ead99e67811 | PRIMARY | pre-specified in 46e0208 |
| assist2012 | fold2 | 2025 | dkt | 4ff6683 | best_valid | slide_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxslide_fold2_2025.csv.gz | 982ecfd8abb7e3df6bc2ee218db3c7c4e176d6b210deae49c14360625f86583e | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold3 | 2026 | dkt | 4ff6683 | final | full | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxfull_fold3_2026.csv.gz | f5840f00f9ed7b43228527f5304b530f94f89c8296a2463f9adb91be77f7cd55 | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold3 | 2026 | dkt | 4ff6683 | final | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxchunk_fold3_2026.csv.gz | 27fbbeaca5fa4c926fcffc813e2e23817535ca11b9abb42de4f10fb9438ee2b1 | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold3 | 2026 | dkt | 4ff6683 | final | slide_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxslide_fold3_2026.csv.gz | d00aff55bfe44c29e03360fdf6d0b18793cb61f1ca98b21458f98c6a45d52f02 | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold3 | 2026 | dkt | 4ff6683 | best_valid | full | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxfull_fold3_2026.csv.gz | e5eed7f95315035ce4e52c19b537d426bac3e1e2fa5475cd0c768b677875369a | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold3 | 2026 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxchunk_fold3_2026.csv.gz | 024fed578f50613bf26813e826eb5ef23d30b9ff63ae2a81b0b8c4ad8158905e | PRIMARY | pre-specified in 46e0208 |
| assist2012 | fold3 | 2026 | dkt | 4ff6683 | best_valid | slide_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxslide_fold3_2026.csv.gz | 47bf7a01572b732c55d04c6fe584177af7f1a2964195f8e0b2b901fcba7bfc8d | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold4 | 2027 | dkt | 4ff6683 | final | full | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxfull_fold4_2027.csv.gz | 97decb50f6418ef0a15d16b19fe92bb878660531a12c0b6e3827bbbd39921684 | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold4 | 2027 | dkt | 4ff6683 | final | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxchunk_fold4_2027.csv.gz | 6ecb99743452c9dea5af8eafb088029a4eff22cce51eae48d9b5e8856200f555 | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold4 | 2027 | dkt | 4ff6683 | final | slide_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_finalxslide_fold4_2027.csv.gz | d02a436539fb65da026ddb088a54afc4c9c0f4cf1f5212c80fc046d0875566dc | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold4 | 2027 | dkt | 4ff6683 | best_valid | full | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxfull_fold4_2027.csv.gz | a42aa44662f4fd8b2c5b13d14849c1d0c7539e5ea63726ef291bb1bdc07ff8bb | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold4 | 2027 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxchunk_fold4_2027.csv.gz | 067a01452732b8faca8d66329332544318c6067cf7dd45f0892ebd0406080f3e | PRIMARY | pre-specified in 46e0208 |
| assist2012 | fold4 | 2027 | dkt | 4ff6683 | best_valid | slide_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxslide_fold4_2027.csv.gz | df995cd4ac4c0b3a6fc7de96ecc1016ac30cde1698e53f2185b482759da3bf9e | SENSITIVITY | pre-specified in 46e0208 |
| assist2012 | fold0 | 42 | tktc | 4ff6683 | best_valid | chunk_le_200 | causal_and_pad_2n | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_tktc_best_validxchunk_fold0_42.csv.gz | 7322ce9c264aa93a4419395f2a6f0898ecc2851ecbb9fd86b4121fa090adc177 | PRIMARY | pre-specified in 46e0208 (T-KT-c decision before B1) |
| assist2012 | fold1 | 2024 | tktc | 4ff6683 | best_valid | chunk_le_200 | causal_and_pad_2n | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_tktc_best_validxchunk_fold1_2024.csv.gz | fa356c93e413a78aa0ce5c7511162402e8bc46fd8f8aa644f5dd28e3ab27c812 | PRIMARY | pre-specified in 46e0208 (T-KT-c decision before B1) |
| assist2012 | fold2 | 2025 | tktc | 4ff6683 | best_valid | chunk_le_200 | causal_and_pad_2n | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_tktc_best_validxchunk_fold2_2025.csv.gz | 083e6e4c1fcc58103fe7bde2f63ae897b5e0e95a575556571896a471b7e5fbe3 | PRIMARY | pre-specified in 46e0208 (T-KT-c decision before B1) |
| assist2012 | fold3 | 2026 | tktc | 4ff6683 | best_valid | chunk_le_200 | causal_and_pad_2n | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_tktc_best_validxchunk_fold3_2026.csv.gz | c0f78bad999cfb36f339023f995a9b32558f416d5655233e06711b499e30ac6d | PRIMARY | pre-specified in 46e0208 (T-KT-c decision before B1) |
| assist2012 | fold4 | 2027 | tktc | 4ff6683 | best_valid | chunk_le_200 | causal_and_pad_2n | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_tktc_best_validxchunk_fold4_2027.csv.gz | 11df44063919ee1bc22e2eb6ab773a1d613f7d006c1ca5c463200b5b851b5b72 | PRIMARY | pre-specified in 46e0208 (T-KT-c decision before B1) |
| assist2012 | fold0 | 42 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_simplekt_best_validxchunk_fold0_42.csv.gz | 16ef93d99dc9237644e6643a4fc2c69dba1bb8c262bb626bd65d5b2bef5571c6 | SENSITIVITY | post-hoc robustness analysis |
| assist2012 | fold1 | 2024 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_simplekt_best_validxchunk_fold1_2024.csv.gz | 9df920cd8f469767ae6d0c99050ca04fb9fa51bd23d2357a2388e6c0c82a5b3e | SENSITIVITY | post-hoc robustness analysis |
| assist2012 | fold2 | 2025 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_simplekt_best_validxchunk_fold2_2025.csv.gz | 9a09c020fc5085a069db61e4beff08b55688a7758c5a42b2443ca8ce29bc7bbc | SENSITIVITY | post-hoc robustness analysis |
| assist2012 | fold3 | 2026 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_simplekt_best_validxchunk_fold3_2026.csv.gz | 2900da79889ed0439ef306ff16760063092b9f8f5d4b8044c49ff76ce89b751d | SENSITIVITY | post-hoc robustness analysis |
| assist2012 | fold4 | 2027 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_simplekt_best_validxchunk_fold4_2027.csv.gz | a736dd25b4126eb0e407c9d1e4184fce9055733a71f61e84639c2a11d706b220 | SENSITIVITY | post-hoc robustness analysis |
| junyi | fold0 | 42 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_junyi_dkt_best_validxchunk_fold0_42.csv.gz | 2a53abadd13cd5952f36a8eacb5f823537c5a62d989873713bb912107e349fb6 | PRIMARY | post-hoc robustness analysis |
| junyi | fold1 | 2024 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_junyi_dkt_best_validxchunk_fold1_2024.csv.gz | cf7a37e90317787ae03c3524e2f7b716e880794efe654f82fa119d1f58f4fd7d | PRIMARY | post-hoc robustness analysis |
| junyi | fold2 | 2025 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_junyi_dkt_best_validxchunk_fold2_2025.csv.gz | 749482ba108461a4b25c6d1ab380704a4fc96c0d5c5ed4729fb1c8e376e64089 | PRIMARY | post-hoc robustness analysis |
| junyi | fold3 | 2026 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_junyi_dkt_best_validxchunk_fold3_2026.csv.gz | e8f0210ab8776d0925fc063831b24ee474dcbda84150bee7d74a518f98dec711 | PRIMARY | post-hoc robustness analysis |
| junyi | fold4 | 2027 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_junyi_dkt_best_validxchunk_fold4_2027.csv.gz | 323ab5d37a8085edd425b9151e3c6c69f92649ecd7adea34bc68a4b860699bf8 | PRIMARY | post-hoc robustness analysis |
| assist2012 | fold5 | 42 | dkt | 4ff6683 | best_valid | chunk_le_200 | lstm_shift_pad0 | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_dkt_best_validxchunk_fold5_42.csv.gz | 6352c86ef556ad3a01673147d3cd6860bdf840675fc2ac4c68bbe764d0757d2f | SENSITIVITY | post-hoc robustness analysis |
| assist2012 | fold5 | 42 | tktc | 4ff6683 | best_valid | chunk_le_200 | causal_and_pad_2n | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_tktc_best_validxchunk_fold5_42.csv.gz | b1fd811d99b2835ca33a4d6f4bfd98ed9cff26674f6122746bc364531d7ceab2 | SENSITIVITY | post-hoc robustness analysis |
| assist2012 | fold5 | 42 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_simplekt_best_validxchunk_fold5_42.csv.gz | 40f377dd783c14c3446a0c29d37c26c0b3efc665ae3e85c22ca1e658975f4e4a | SENSITIVITY | post-hoc robustness analysis |
| assist2012 | fold0 | 42 | tkt_pe | 4ff6683 | best_valid | chunk_le_200 | causal_pad_2n_plus_position | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_assist2012_tkt_pe_best_validxchunk_fold0_42.csv.gz | b3ae7f2a02284153348620680e87f3ab8d88f77434fd429802068e6bdcaddaa8 | SENSITIVITY | post-hoc robustness analysis |
| junyi | fold0 | 42 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_junyi_simplekt_best_validxchunk_fold0_42.csv.gz | ead071dc0ea5c350e5a6fb6c4b9981ce6a62c74f7ad3ba5c03d128798706973d | SENSITIVITY | post-hoc robustness analysis |
| junyi | fold1 | 2024 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_junyi_simplekt_best_validxchunk_fold1_2024.csv.gz | d7b8fa77529e96fc2c4b441a60e00b26fe4952f0ea0311795b8d1774a1be18e8 | SENSITIVITY | post-hoc robustness analysis |
| junyi | fold2 | 2025 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_junyi_simplekt_best_validxchunk_fold2_2025.csv.gz | dbb1fb72ebc306f976fae6f427e16d83639ead001763ec0d4f22e96f7f12d63a | SENSITIVITY | post-hoc robustness analysis |
| junyi | fold3 | 2026 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_junyi_simplekt_best_validxchunk_fold3_2026.csv.gz | 126ca58f4d66b14b305685c7608cfafeaf5ecd991eaa3ff7e8262fe8e19cf354 | SENSITIVITY | post-hoc robustness analysis |
| junyi | fold4 | 2027 | simplekt | 4ff6683 | best_valid | chunk_le_200 | pykt_causal_attention | train-only f_train; cuts 0/20/100/500 | ECE 15 equal-width; no_history=0 | pred_junyi_simplekt_best_validxchunk_fold4_2027.csv.gz | 3033c91975659ec64e6b1dc26647bd190ffc071b587364c875971c3a53f23811 | SENSITIVITY | post-hoc robustness analysis |
