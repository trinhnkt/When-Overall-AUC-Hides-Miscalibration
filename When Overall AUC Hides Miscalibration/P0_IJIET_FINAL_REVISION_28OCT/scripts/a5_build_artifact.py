#!/usr/bin/env python3
"""Assemble P0_IJIET_FINAL_REVISION_28OCT/artifact_v4 from commit 4ff6683 and local exports."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INNER = Path(__file__).resolve().parents[2]
ART = INNER / "P0_IJIET_FINAL_REVISION_28OCT" / "artifact_v4"
PRED_SRC = INNER / "results" / "predictions"
COMMIT = "4ff66835561e2597a50197dcfb93aba1ec74583b"
PAIRS = ((0, 42), (1, 2024), (2, 2025), (3, 2026), (4, 2027))
ROWS: list[tuple[str, str, str, str]] = []


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record(path: Path, role: str, source: str, coverage: str) -> None:
    rel = path.relative_to(ART).as_posix()
    ROWS.append((rel, str(path.stat().st_size), sha256(path), role, source, coverage))
    print(f"FILE {rel}", flush=True)


def copy_file(src: Path, dest: Path, role: str, source: str, coverage: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = src.stat().st_size
    if not dest.is_file() or dest.stat().st_size != size or (size < 50_000_000 and dest.read_bytes() != src.read_bytes()):
        shutil.copy2(src, dest)
    record(dest, role, source, coverage)


def pred(dataset: str, model: str, select: str, context: str, fold: int, seed: int) -> str:
    return f"pred_{dataset}_{model}_{select}x{context}_fold{fold}_{seed}.csv.gz"


def extract_commit() -> None:
    archive = ART / "_commit.tar"
    ART.mkdir(parents=True, exist_ok=True)
    paths = [
        "sparse-calibration-kt/src",
        "sparse-calibration-kt/tests",
        "sparse-calibration-kt/scripts",
        "sparse-calibration-kt/configs",
        "sparse-calibration-kt/docs/analysis_plan_P0_v2.md",
        "sparse-calibration-kt/requirements.txt",
        "sparse-calibration-kt/requirements-lock.txt",
    ]
    subprocess.run(
        ["git", "-C", str(REPO), "archive", "--format=tar", "-o", str(archive), COMMIT, "--", *paths],
        check=True,
    )
    with tarfile.open(archive) as bundle:
        bundle.extractall(ART / "_commit")
    archive.unlink()
    snap = ART / "_commit" / "sparse-calibration-kt"
    code = ART / "code"
    if code.exists():
        shutil.rmtree(code)
    code.mkdir()
    for name in ("src", "tests", "scripts", "requirements.txt", "requirements-lock.txt"):
        shutil.move(str(snap / name), str(code / name))
    docs = code / "docs"
    docs.mkdir()
    shutil.move(str(snap / "docs" / "analysis_plan_P0_v2.md"), str(docs / "analysis_plan_P0_v2.md"))
    configs = ART / "configs"
    if configs.exists():
        shutil.rmtree(configs)
    shutil.move(str(snap / "configs"), str(configs))
    shutil.rmtree(ART / "_commit")
    note = code / "COMMIT.txt"
    note.write_text(
        COMMIT
        + "\n2026-10-21 16:03:08 +0700\n"
        + "Correct the ASSISTments dense item-support median in Table 8.\n"
        + "The analysis plan in code/docs/analysis_plan_P0_v2.md is the tree at this commit.\n"
        + "Its parent 46e0208, 2026-10-21 16:02:55 +0700, locked that plan before the supplementary runs.\n"
        + "src/ece_uncertainty.py in this snapshot keeps a prefix of the concatenated dense rows.\n"
        + "The published size-matched gap uses a second without-replacement sample of exactly N rows.\n"
        + "That function is rebuild/published_gap.py. Do not recompute G from the snapshot function.\n",
        encoding="utf-8",
    )
    seeds = configs / "SEEDS.txt"
    seeds.write_text(
        "The five scored runs are not the seed list inside the YAML files.\n"
        "fold 0 init_seed 42\n"
        "fold 1 init_seed 2024\n"
        "fold 2 init_seed 2025\n"
        "fold 3 init_seed 2026\n"
        "fold 4 init_seed 2027\n"
        "Fold 2 and fold 3 are one learner partition.\n"
        "Size-match and fold-0 bootstrap seed: 20261021\n"
        "Point estimate draws R = 2000. Bootstrap B = 2000. Inner draws = 200.\n",
        encoding="utf-8",
    )


def add_tree(root: Path, role: str, source: str, coverage: str) -> None:
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        record(path, role, source, coverage)


def predictions() -> None:
    jobs = []
    for fold, seed in PAIRS:
        for select, context in (
            ("best_valid", "chunk"),
            ("best_valid", "full"),
            ("final", "chunk"),
            ("final", "full"),
        ):
            jobs.append((pred("assist2012", "dkt", select, context, fold, seed), "prediction export, ASSISTments DKT, Table A2 cell", "recomputed from this export, folds 0-4"))
        jobs.append((pred("assist2012", "tktc", "best_valid", "chunk", fold, seed), "prediction export, masked T-KT, primary protocol", "recomputed from this export, folds 0-4"))
        jobs.append((pred("assist2012", "simplekt", "best_valid", "chunk", fold, seed), "prediction export, simpleKT, Table 4 only", "AUC and accuracy recomputed from this export, folds 0-4"))
        jobs.append((pred("junyi", "dkt", "best_valid", "chunk", fold, seed), "prediction export, Junyi DKT, post-hoc rows of Tables 4 and 5", "recomputed from this export, folds 0-4; focal group is medium"))
    for name, role, coverage in jobs:
        src = PRED_SRC / name
        if not src.is_file():
            raise SystemExit(f"MISSING {src}")
        copy_file(src, ART / "predictions" / name, role, str(src.relative_to(INNER)).replace("\\", "/"), coverage)


def logs() -> None:
    for src in sorted((INNER / "runs").rglob("train_log.csv")):
        rel = src.relative_to(INNER / "runs").as_posix()
        copy_file(src, ART / "logs" / "training" / rel, "per-run training log", str(src.relative_to(INNER)).replace("\\", "/"), "archived log; weights are not in this artifact")
    a1 = INNER / "P0_IJIET_FINAL_REVISION_28OCT" / "audit" / "A1_DKT_TOKEN0_LOG.txt"
    copy_file(a1, ART / "logs" / "A1_DKT_TOKEN0_LOG.txt", "A1 token-0 log", "P0_IJIET_FINAL_REVISION_28OCT/audit/A1_DKT_TOKEN0_LOG.txt", "verification log; not a training run")
    manifest = INNER / "runs" / "manifest.csv"
    if manifest.is_file():
        copy_file(manifest, ART / "logs" / "manifest.csv", "run manifest", "runs/manifest.csv", "index of scored runs; not a substitute for the prediction exports")


def statistics() -> None:
    mapping = {
        "A5_uncertainty_dkt_assist.csv": "archived DKT uncertainty summary",
        "B1_tktc_uncertainty.csv": "archived masked T-KT uncertainty summary",
        "B2_junyi_dkt_uncertainty.csv": "archived Junyi DKT uncertainty summary",
        "A4_dkt_2x2.csv": "archived DKT checkpoint-by-window summary",
    }
    for name, role in mapping.items():
        src = INNER / "results" / name
        copy_file(
            src,
            ART / "statistics" / "archived" / name,
            role,
            f"results/{name}",
            "archived summary; the reproduce command does not read this file",
        )
    note = ART / "statistics" / "COVERAGE.txt"
    note.write_text(
        "Folds 0, 1, 2, 3, and 4 of every prediction file in predictions/ are recomputed from those exports.\n"
        "Fold 2 and fold 3 remain one learner partition in the four-partition mean.\n"
        "Fold 5 is not in this artifact.\n"
        "The slide window is not in this artifact.\n"
        "XES3G5M predictions are not in this artifact. Table 4 marks that dataset Not evaluated.\n"
        "Junyi simpleKT predictions are not in this artifact.\n"
        "Unmasked T-KT predictions are not in this artifact.\n"
        "Tables A3 and A4 are recomputed from the ASSISTments DKT and T-KT masked exports (best validation, window 200).\n"
        "Table A1 is recomputed from the DKT, T-KT masked, simpleKT, and Junyi DKT exports; its base-rate rows apply\n"
        "the constants in predictions/base_rate_constants.csv to the DKT rows of the same partition.\n"
        "The G column of Table A5 is recomputed by reproduce_tables.py; the supplementary intervals by partition_intervals.py.\n"
        "Tables 6 and 7 need the split files, which are not in this artifact; statistics/recorded/TABLE6_7_CONTEXT.json\n"
        "is the recorded output of scripts_28oct/table6_context.py.\n"
        "Model weights are not in this artifact. The command does not retrain.\n"
        "Archived CSV files in statistics/archived are the earlier summaries. reproduce_tables.py does not read them.\n",
        encoding="utf-8",
    )
    record(note, "coverage statement", "this build", "folds 0-4 are prediction-reproducible; fold 5 and XES are absent")


def rebuild_files() -> None:
    here = Path(__file__).resolve().parent
    dest = ART / "rebuild"
    dest.mkdir(parents=True, exist_ok=True)
    for name, target_name in (
        ("a5_published_gap.py", "published_gap.py"),
        ("a5_far_brier.py", "far_brier.py"),
        ("a5_reproduce_tables.py", "reproduce_tables.py"),
        ("c1_partition_intervals.py", "partition_intervals.py"),
    ):
        shutil.copy2(here / name, dest / target_name)
    note = dest / "README.txt"
    note.write_text(
        "From the artifact root:\n\n"
        "    py -3 rebuild/reproduce_tables.py\n\n"
        "published_gap.py is the random-subset size match and the fold-0 learner-cluster bootstrap.\n"
        "far_brier.py is FAR at tau = 0.7, its fold-0 KC-clustered bootstrap, and the 15-bin Brier decomposition (Tables A1, A3, A4).\n"
        "reproduce_tables.py also checks the 16 rows of Table A1 (N, AUC, ACC, Brier, UNC, REL, RES) and the G column of Table A5.\n"
        "The base-rate rows of Table A1 use predictions/base_rate_constants.csv.\n\n"
        "The supplementary Table A5 intervals for folds 1, 2-3, and 4 are a separate command (about 5 minutes each):\n\n"
        "    py -3 rebuild/partition_intervals.py points dkt\n"
        "    py -3 rebuild/partition_intervals.py points tktc\n"
        "    py -3 rebuild/partition_intervals.py boot dkt 1      (also: dkt 23, dkt 4, tktc 1, tktc 23, tktc 4)\n"
        "    py -3 rebuild/partition_intervals.py combine\n\n"
        "Output: statistics/partition_intervals/C1_PARTITION_INTERVALS.csv. The recorded run is statistics/recorded/C1_PARTITION_INTERVALS.csv.\n"
        "code/src/ece_uncertainty.py is the 4ff6683 prefix version and is not called by these commands.\n",
        encoding="utf-8",
    )


R28 = INNER / "P0_IJIET_FINAL_REVISION_28OCT"
SCRIPTS_28OCT = (
    "msedit.py", "fmt_check.py", "b5_stratified_metrics.py", "b5_edit_manuscript.py", "c1_partition_intervals.py",
    "table6_context.py", "a4_c1_edit_manuscript.py", "b3_rq3_from_table_a2.py", "b6_model_claims.py",
    "b7_text_cleanup.py", "b2_notation.py", "b2_fig3.py", "b1_abstract.py", "c3_reference21.py",
    "c3_springer_meta.py", "c3_template_scan.py", "a6_final_blind_qa.py", "art_base_rate_constants.py",
    "b2_notation_followup.py", "art_data_availability.py", "gate_claim_evidence.py",
)
RECORDED = (
    ("results/B5_STRATIFIED_METRICS.csv", "B5 group-level metrics, per run and four-partition"),
    ("results/C1_PARTITION_INTERVALS.csv", "Table A5 recorded run"),
    ("results/TABLE6_7_CONTEXT.json", "Tables 6 and 7 descriptors from the split files"),
    ("results/B3_TABLE_A2_EFFECTS.csv", "checkpoint and window effects derived from Table A2"),
    ("results/fig3_primary_protocol_fold0.png", "Fig. 3 image in the manuscript"),
)


def extras() -> None:
    copy_file(R28 / "results" / "base_rate_constants.csv", ART / "predictions" / "base_rate_constants.csv",
              "base-rate constant per partition (Table A1 reference rows)",
              "P0_IJIET_FINAL_REVISION_28OCT/results/base_rate_constants.csv from results/predictions/*_irt_1pl_*_rerun.csv",
              "constant p, source sha256, and test-learner check; the 3.6 GB IRT files are not shipped")
    for rel, role in RECORDED:
        src = R28 / rel
        copy_file(src, ART / "statistics" / "recorded" / src.name, role, "P0_IJIET_FINAL_REVISION_28OCT/" + rel,
                  "recorded output; reproduce_tables.py does not read it")
    for src in sorted((R28 / "results" / "C1").glob("*.json")) + sorted((R28 / "results" / "C1").glob("points_*.csv")):
        copy_file(src, ART / "statistics" / "recorded" / "C1" / src.name, "Table A5 recorded intermediate",
                  "P0_IJIET_FINAL_REVISION_28OCT/results/C1/" + src.name, "recorded output of partition_intervals.py")
    for name in SCRIPTS_28OCT:
        copy_file(R28 / "scripts" / name, ART / "scripts_28oct" / name, "28 Oct revision script",
                  "P0_IJIET_FINAL_REVISION_28OCT/scripts/" + name,
                  "edits or derives manuscript text; needs the manuscript or split files, which are not in this artifact")
    copy_file(INNER / "P0_IJIET_FINAL_CORRECTION_2026" / "artifact_final" / "04_audits" / "GATE_B_XES_REPORT.md",
              ART / "audits" / "GATE_B_XES_REPORT.md", "XES3G5M leakage audit (L8)",
              "P0_IJIET_FINAL_CORRECTION_2026/artifact_final/04_audits/GATE_B_XES_REPORT.md",
              "cited in Section IV.B; XES3G5M stays descriptive only")
    copy_file(INNER / "manuscript-pack" / "analysis" / "xes_padding_counts.csv", ART / "audits" / "xes_padding_counts.csv",
              "XES3G5M padding and repeat counts", "manuscript-pack/analysis/xes_padding_counts.csv",
              "cited in Section III.A (is_repeat_nonzero = 863807)")


def tests_copy() -> None:
    src = ART / "code" / "tests"
    dest = ART / "tests"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def write_readme() -> None:
    text = """# Artifact v4

Code snapshot: commit 4ff66835561e2597a50197dcfb93aba1ec74583b (2026-10-21 16:03:08 +0700).

The analysis plan in `code/docs/analysis_plan_P0_v2.md` was locked in the parent commit 46e0208 at 2026-10-21 16:02:55 +0700, before the first supplementary training log (2026-10-21 21:58). That plan is the timestamped pre-result plan for the ASSISTments DKT checkpoint-by-window grid and for the masked T-KT correction. Junyi DKT, simpleKT, and fold 5 were added after that plan.

## One command

From this directory:

    py -3 rebuild/reproduce_tables.py

The command does not train. It reads `predictions/` and checks the supported digits in Table 4, Table 5, and Table A2, including the size-matched gaps, the fold-0 intervals, and the rounded counts. It also checks Table A1 (group-level N, AUC, ACC, and the 15-bin Brier decomposition), Tables A3 and A4 (FAR at tau = 0.7) for ASSISTments DKT and T-KT masked, and the G column of Table A5. The supplementary Table A5 intervals are a separate command; see `rebuild/README.txt`.

## Primary protocol

The manuscript's primary protocol has the internal ID P0-BV200-15EW: the validation-AUC checkpoint, non-overlapping test windows of at most 200 responses, and M = 15 equal-width bins, scored on rows with a nonempty test history. The manuscript calls it "the primary protocol".

## What the prediction exports cover

Every included export has folds 0, 1, 2, 3, and 4. Those folds are recomputed from the exports. This artifact is not a fold-0-only package.

| Export | Used for |
| --- | --- |
| ASSISTments DKT, final and best validation, full history and window 200 | Table A2, and the primary row of Tables 4, 5, A1, A3, A4, and A5 |
| ASSISTments T-KT masked, best validation, window 200 | Tables 4, 5, A1, A3, A4, and A5 |
| ASSISTments simpleKT, best validation, window 200 | Table 4 and the sensitivity rows of Table A1 |
| Junyi DKT, best validation, window 200 | post-hoc rows of Tables 4, 5, and A1; the focal group is medium |
| `base_rate_constants.csv` | base-rate rows of Table A1: the constant prediction of each IRT rerun, applied to the DKT rows of the same partition; source hashes and the test-learner check are in the file |

## Other folders

- `statistics/recorded/`: recorded outputs of the 28 Oct revision (Table A1 source metrics, Table A5 run, Tables 6 and 7 descriptors, Table A2 effects, Fig. 3 image). The one command does not read them.
- `scripts_28oct/`: scripts that derived or edited the 28 Oct manuscript text. They need the manuscript or the split files, which are not in this artifact.
- `audits/`: the XES3G5M leakage report (`GATE_B_XES_REPORT.md`) and padding counts (`xes_padding_counts.csv`) cited in Sections III.A and IV.B.

Fold 2 and fold 3 are averaged before the four-partition standard deviation.

## What this artifact does not support

- Retraining. The raw datasets and the model weights are absent.
- Fold 5.
- The slide window.
- XES3G5M. Table 4 already marks it Not evaluated.
- Recomputing Tables 6 and 7. They need the processed split files, which are not shipped.
- Junyi simpleKT.
- Unmasked T-KT.
- Recomputing the published gap from `code/src/ece_uncertainty.py`. That 4ff6683 function keeps a prefix of the concatenated dense rows. The published gap keeps exactly N rows by a second sample without replacement. The command uses `rebuild/published_gap.py`.

## Seeds

`configs/SEEDS.txt`. The YAML files do not list the five scored initialization seeds. The size-match and bootstrap seed is 20261021.

## Logs

`logs/training/` holds the per-run training logs. `logs/A1_DKT_TOKEN0_LOG.txt` is the token-0 check. `logs/UT_A1_A7_TKT_MASKED.txt` is the masked T-KT unit-test run. `tests/` is the test file from commit 4ff6683.
"""
    (ART / "README.md").write_text(text, encoding="utf-8")


def run_tests() -> None:
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ART / "code")
    env["PYTHONIOENCODING"] = "utf-8"
    script = (
        "import sys\n"
        "from tests.test_protocol_v2 import (\n"
        " test_ut_a1_past_predictions_ignore_current_label,\n"
        " test_ut_a2_future_labels_do_not_change_current_prediction,\n"
        " test_ut_a3_prefix_matches_masked_full_chunk,\n"
        " test_ut_a4_trailing_pad_does_not_change_valid_positions,\n"
        " test_ut_a5_target_of_position_i_is_the_next_row,\n"
        " test_ut_a6_short_fit_loss_is_finite_and_falls,\n"
        " test_ut_a7_previous_label_changes_the_prediction,\n"
        ")\n"
        "pairs = [\n"
        " ('UT-A1', test_ut_a1_past_predictions_ignore_current_label),\n"
        " ('UT-A2', test_ut_a2_future_labels_do_not_change_current_prediction),\n"
        " ('UT-A3', test_ut_a3_prefix_matches_masked_full_chunk),\n"
        " ('UT-A4', test_ut_a4_trailing_pad_does_not_change_valid_positions),\n"
        " ('UT-A5', test_ut_a5_target_of_position_i_is_the_next_row),\n"
        " ('UT-A6', test_ut_a6_short_fit_loss_is_finite_and_falls),\n"
        " ('UT-A7', test_ut_a7_previous_label_changes_the_prediction),\n"
        "]\n"
        "for name, fn in pairs:\n"
        "    fn()\n"
        "    print(name + ' = PASS', flush=True)\n"
        "print('UT_A1_A7 = PASS', flush=True)\n"
    )
    log = ART / "logs" / "UT_A1_A7_TKT_MASKED.txt"
    completed = subprocess.run(
        ["py", "-3", "-c", script],
        cwd=str(ART),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        print(log.read_text(encoding="utf-8"))
        raise SystemExit(f"UT-A tests failed with code {completed.returncode}")
    record(log, "UT-A1 through UT-A7 log for masked T-KT", "tests/test_protocol_v2.py at " + COMMIT, "unit tests on synthetic sequences; not a training run")


def manifest() -> None:
    add_tree(ART / "code", "code at commit 4ff6683", COMMIT, "snapshot; the prefix size-match in this tree is not the published gap")
    add_tree(ART / "configs", "model config or seed list", COMMIT + " plus SEEDS.txt", "YAML from the commit; scored seeds are in SEEDS.txt")
    add_tree(ART / "tests", "masked T-KT unit tests from commit 4ff6683", COMMIT, "UT-A1 through UT-A7 and the other tests in that file")
    add_tree(ART / "rebuild", "recompute command", "P0_IJIET_FINAL_REVISION_28OCT/scripts/a5_reproduce_tables.py", "reproduces the supported table digits without training")
    lines = ["relative_path,bytes,sha256,role,source,coverage"]
    for row in ROWS:
        lines.append(",".join('"' + part.replace('"', '""') + '"' for part in row))
    # README is recorded after it is written, then the manifest includes it.
    readme = ART / "README.md"
    lines.append(
        ",".join(
            '"' + part.replace('"', '""') + '"'
            for part in (
                "README.md",
                str(readme.stat().st_size),
                sha256(readme),
                "package description",
                "this build",
                "states the supported and unsupported claims",
            )
        )
    )
    (ART / "MANIFEST.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"MANIFEST {len(lines) - 1} files", flush=True)


def main() -> None:
    extract_commit()
    tests_copy()
    rebuild_files()
    statistics()
    logs()
    predictions()
    extras()
    run_tests()
    write_readme()
    manifest()
    print("BUILD DONE", flush=True)


if __name__ == "__main__":
    main()
