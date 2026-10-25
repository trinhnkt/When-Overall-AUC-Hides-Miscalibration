#!/usr/bin/env python3
"""Build artifact_final and the scrubbed blind submission copy."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd
from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
CORR = ROOT / "P0_IJIET_FINAL_CORRECTION_2026"
ART = CORR / "artifact_final"
PRED = ROOT / "results" / "predictions"
TITLE = (
    "When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing "
    "on Rarely Practiced Knowledge Components"
)
BLIND = ROOT / "manuscript-pack" / "manuscript" / f"{TITLE}_blind.docx"
NAMED = ROOT / "manuscript-pack" / "manuscript" / f"{TITLE}.docx"
PAIRS = ((0, 42, "P0"), (1, 2024, "P1"), (2, 2025, "P2"), (3, 2026, "P2"), (4, 2027, "P4"))
EXPORTS = [
    ("assist2012", "dkt", "pred_assist2012_dkt_best_validxchunk_fold{fold}_{seed}.csv.gz"),
    ("assist2012", "tktc", "pred_assist2012_tktc_best_validxchunk_fold{fold}_{seed}.csv.gz"),
    ("junyi", "dkt", "pred_junyi_dkt_best_validxchunk_fold{fold}_{seed}.csv.gz"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT.parent, text=True
        ).strip()
    except Exception as exc:
        return f"UNAVAILABLE {exc}"


def write_splits() -> None:
    out = ART / "01_splits"
    rows = [{"fold": fold, "init_seed": seed, "unique_partition": part} for fold, seed, part in PAIRS]
    pd.DataFrame(rows).to_csv(out / "seed_fold_partition.csv", index=False)
    (out / "README.md").write_text(
        "Primary design: learner-disjoint train, validation, and test.\n"
        "Fold 2 and fold 3 are one learner partition (P2) with two initialization seeds.\n"
        "Temporal splits, where the folder exists, are listed separately and are not primary partitions.\n"
        "XES3G5M learner ids are not a model-evidence split. Model scores for XES were not exported.\n",
        encoding="utf-8",
    )
    for dataset in ("assist2012", "junyi"):
        for fold, _, part in PAIRS:
            for split in ("train", "valid", "test"):
                src = (
                    ROOT / "data" / "processed" / dataset / "splits"
                    / "learner_based" / f"fold_{fold}" / f"{split}.csv"
                )
                if not src.is_file():
                    continue
                header = pd.read_csv(src, nrows=0).columns
                col = "user_id" if "user_id" in header else ("uid" if "uid" in header else header[0])
                ids = pd.read_csv(src, usecols=[col])[col].drop_duplicates()
                dest = out / dataset / f"{part}_fold{fold}" / f"{split}_learner_ids.csv"
                dest.parent.mkdir(parents=True, exist_ok=True)
                ids.to_csv(dest, index=False, header=["learner_id"])
        temporal = ROOT / "data" / "processed" / dataset / "splits" / "temporal"
        if temporal.is_dir():
            note = out / "temporal" / dataset
            note.mkdir(parents=True, exist_ok=True)
            (note / "KEPT_SEPARATE.txt").write_text(
                f"Temporal files exist at {temporal}. They are not one of the four learner partitions.\n",
                encoding="utf-8",
            )


def write_training() -> None:
    out = ART / "02_training"
    out.mkdir(parents=True, exist_ok=True)
    for name in ("assist2012.yaml", "junyi.yaml"):
        src = ROOT / "configs" / name
        if src.is_file():
            shutil.copy(src, out / name)
    simple = ROOT / "scripts" / "p0_retrain_official_simplekt.py"
    if simple.is_file():
        shutil.copy(simple, out / "simplekt_run_script.py")
    rows = []
    specs = [
        ("assist2012", "dkt", "runs/a_dkt/assist2012_fold{fold}_seed{seed}_{which}"),
        ("assist2012", "tktc", "runs/b1_tktc/assist2012_fold{fold}_seed{seed}_{which}"),
        ("junyi", "dkt", "runs/b2_dkt_junyi/junyi_fold{fold}_seed{seed}_{which}"),
    ]
    for dataset, model, pattern in specs:
        for fold, seed, part in PAIRS:
            for which in ("best_valid", "final"):
                folder = ROOT / pattern.format(fold=fold, seed=seed, which=which)
                log = folder / "train_log.csv"
                pt = folder / "model.pt"
                if log.is_file():
                    dest = out / "logs" / f"{dataset}_{model}_fold{fold}_{which}_train_log.csv"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(log, dest)
                rows.append({
                    "dataset": dataset,
                    "model": model,
                    "fold": fold,
                    "init_seed": seed,
                    "unique_partition": part,
                    "checkpoint": which,
                    "log": str(log.relative_to(ROOT)) if log.is_file() else "MISSING",
                    "checkpoint_sha256": sha256(pt) if pt.is_file() else "MISSING",
                })
                print(dataset, model, fold, which, "hashed" if pt.is_file() else "missing", flush=True)
    pd.DataFrame(rows).to_csv(out / "checkpoint_hashes.csv", index=False)
    (out / "RUN_COMMANDS.md").write_text(
        "These commands are the recorded entry points. This package does not retrain.\n\n"
        "ASSISTments DKT and T-KT masked use configs/assist2012.yaml.\n"
        "Junyi DKT uses configs/junyi.yaml and is post-hoc.\n"
        "simpleKT uses scripts/p0_retrain_official_simplekt.py and is sensitivity.\n"
        "XES3G5M was not trained. There is no corrected checkpoint.\n"
        "The primary checkpoint is best_valid. The final checkpoint is sensitivity for the DKT grid.\n",
        encoding="utf-8",
    )


def write_predictions() -> None:
    out = ART / "03_predictions"
    out.mkdir(parents=True, exist_ok=True)
    checksums = []
    for dataset, model, pattern in EXPORTS:
        for fold, seed, part in PAIRS:
            src = PRED / pattern.format(fold=fold, seed=seed)
            dest = out / f"{dataset}_{model}_fold{fold}_seed{seed}.csv.gz"
            print("export", dest.name, flush=True)
            first = True
            for chunk in pd.read_csv(src, chunksize=200000):
                keep = pd.DataFrame({
                    "learner_id": chunk["user_id"],
                    "response_id": chunk["event_id"] if "event_id" in chunk.columns else chunk["row_index"],
                    "item_id": chunk["item_id"],
                    "kc_id": chunk["kc_id"],
                    "sequence_index": chunk["seq_pos"],
                    "y_true": chunk["y"],
                    "p_hat": chunk["p"],
                    "partition": part,
                    "fold": fold,
                    "model": model,
                    "protocol_id": "P0-BV200-15EW",
                    "no_history": chunk["no_history"],
                    "group": chunk["group"],
                })
                keep.to_csv(dest, mode="wt" if first else "at", index=False, header=first, compression="gzip")
                first = False
            checksums.append({
                "file": dest.name,
                "sha256": sha256(dest),
                "source": str(src.relative_to(ROOT)),
                "source_sha256": sha256(src),
            })
    pd.DataFrame(checksums).to_csv(out / "checksums.csv", index=False)


def scrub_color(element) -> int:
    n = 0
    for node in element.iter():
        if node.tag == qn("w:color") and (node.get(qn("w:val")) or "").upper() == "FF0000":
            node.set(qn("w:val"), "000000")
            n += 1
    return n


def scrub_docx(src: Path, dest: Path) -> dict:
    doc = Document(src)
    props = doc.core_properties
    props.author = ""
    props.last_modified_by = ""
    props.title = TITLE
    props.subject = ""
    props.category = ""
    props.comments = ""
    props.identifier = ""
    n = scrub_color(doc.element)
    for section in doc.sections:
        n += scrub_color(section.header._element)
        n += scrub_color(section.footer._element)
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc.save(dest)
    # Drop comment and custom-property parts from the saved zip when present.
    tmp = dest.with_suffix(".tmp.docx")
    drop = {"word/comments.xml", "docProps/custom.xml"}
    with zipfile.ZipFile(dest, "r") as zin, zipfile.ZipFile(tmp, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in drop:
                continue
            if item.filename == "word/_rels/document.xml.rels":
                text = data.decode("utf-8")
                if "comments" in text:
                    text = "\n".join(line for line in text.splitlines() if "comments" not in line)
                    data = text.encode("utf-8")
            zout.writestr(item, data)
    tmp.replace(dest)
    red_left = 0
    with zipfile.ZipFile(dest) as zf:
        for name in zf.namelist():
            if name.endswith(".xml"):
                red_left += zf.read(name).decode("utf-8", errors="ignore").upper().count("FF0000")
    return {"red_recolored": n, "ff0000_left": red_left}


def write_submission(blind_stats: dict) -> None:
    out = ART / "07_submission"
    out.mkdir(parents=True, exist_ok=True)
    letter = f"""Cover letter — International Journal of Information and Education Technology

Manuscript: {TITLE}
Date: 25 October 2026

Dear Editor,

Please consider the enclosed manuscript. It is an evaluation protocol for
knowledge-tracing probabilities, not a new tracing model.

The primary scores use protocol P0-BV200-15EW on ASSISTments 2012:
a validation-AUC checkpoint, non-overlapping test windows of at most 200,
15 equal-width bins, and four unique learner partitions. The primary models
are DKT and a causally masked Transformer. Their sparse ECE is higher than
their dense ECE. On fold 0 the size-matched gap has a learner-cluster 95%
interval that excludes 0. The bias reference ΔECE* is reported separately
and is not a significance test. The fold-0 interval is not a claim about
all four partitions.

Junyi Academy has no sparse group. Its DKT contrast is post-hoc. XES3G5M
is a descriptive audit only: leakage check L8 failed, and no corrected
model was trained. The paper does not claim that the result is replicated
on three datasets, and it does not use archived final-checkpoint pairs as
the current result.

The named file is for the editorial office. Please send reviewers only the
blind file. There is no separate supplementary PDF. Appendix tables A1, A3,
and A4 are archived probes and are labeled as such. Table A2 is the DKT
sensitivity grid.

Ethics and the generative-AI statement are in the manuscript. They still
require confirmation by every author before submission. This letter does
not assert that confirmation.

For the editorial office only, the repository is
https://github.com/trinhnkt/When-Overall-AUC-Hides-Miscalibration.
That address is not in the blind manuscript.

Sincerely,
Van-Hau Nguyen
"""
    (out / "cover_letter.txt").write_text(letter, encoding="utf-8")
    (ROOT / "manuscript-pack" / "output" / "OJS_UPLOAD" / "cover_letter_ijiet.txt").write_text(letter, encoding="utf-8")
    (out / "AI_DISCLOSURE_CHECKLIST.md").write_text(
        "The manuscript contains a generative-AI statement: Cursor was used for language and checking; "
        "AI is not a co-author; the authors remain responsible.\n\n"
        "CONFIRMED BY ALL AUTHORS IN THIS SESSION: NO.\n"
        "Do not treat the statement as a new sign-off.\n",
        encoding="utf-8",
    )
    (out / "ETHICS_CHECKLIST.md").write_text(
        "The manuscript states that the study is a secondary analysis of three public, provider-de-identified logs, "
        "with no new recruitment and no classroom trial.\n\n"
        "CONFIRMED BY ALL AUTHORS IN THIS SESSION: NO.\n"
        "No ethics protocol number was invented.\n",
        encoding="utf-8",
    )
    (out / "SUBMISSION_CHECKLIST.md").write_text(
        "Title punctuation remains the hyphen. It was not changed to a colon.\n"
        "No CC BY line was added. No DOI, volume, issue, or acceptance date was invented.\n"
        "Blind Word red-recolor count and remaining FF0000 hits: "
        f"{blind_stats}.\n"
        "Separate supplementary PDF: none. See SUPPLEMENTARY_README.md.\n"
        "Ready to submit: NO. Author confirmation and a full reference check are still open.\n",
        encoding="utf-8",
    )
    (out / "SUPPLEMENTARY_README.md").write_text(
        "There is no separate supplementary document.\n\n"
        "Appendix Table A2 is the DKT sensitivity grid and can be rebuilt from results/A4_dkt_2x2.csv.\n"
        "Appendix Tables A1, A3, and A4 are archived. They are NOT REPRODUCIBLE as primary-protocol results "
        "because those probes were not recomputed on the locked predictions.\n"
        "Fig. 1 is a workflow drawing and is NOT REPRODUCIBLE from the prediction files.\n"
        "Fig. 3 is reproducible from the fold-0 primary prediction files by scripts/p0_gate_d_rebuild.py.\n",
        encoding="utf-8",
    )


def write_rebuild() -> None:
    out = ART / "06_rebuild"
    out.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_text(
        "From the project root:\n\n"
        "    py -3 -u scripts/p0_gate_d_rebuild.py\n\n"
        "That command rewrites Tables 2, 4, 5, 6, and A2 and redraws Fig. 3 "
        "from the prediction files and the Gate C tables.\n\n"
        "NOT REPRODUCIBLE from that command:\n"
        "- Table A1 Murphy decomposition under the primary protocol\n"
        "- Tables A3 and A4 (FAR was not recomputed)\n"
        "- Fig. 1 workflow drawing\n"
        "- Fig. 2 frequency chart\n"
        "- XES model metrics (not evaluated)\n",
        encoding="utf-8",
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if ART.exists():
        shutil.rmtree(ART)
    for name in (
        "00_manifest", "01_splits", "02_training", "03_predictions",
        "04_audits", "05_statistics", "06_rebuild", "07_submission",
    ):
        (ART / name).mkdir(parents=True, exist_ok=True)
    sha = git_sha()
    (ART / "00_manifest" / "GIT_SHA.txt").write_text(
        sha + "\nWorking tree contains uncommitted Gate D and Gate E edits. This SHA is HEAD only.\n",
        encoding="utf-8",
    )
    for name in ("requirements.txt", "requirements-lock.txt"):
        src = ROOT / name
        if src.is_file():
            shutil.copy(src, ART / "00_manifest" / name)
    (ART / "00_manifest" / "DATA_PROVENANCE.md").write_text(
        "ASSISTments 2012, Junyi Academy, and XES3G5M are public releases from their providers.\n"
        "Processed learner-based splits used here are under data/processed/<dataset>/splits/learner_based/.\n"
        "The artifact stores learner ids, not the raw logs.\n"
        "XES3G5M question-level files were audited for Gate B and were not used to train a model.\n",
        encoding="utf-8",
    )
    shutil.copy(ROOT / "docs" / "claim_evidence.csv", ART / "00_manifest" / "claim_evidence.csv")
    write_splits()
    write_training()
    write_predictions()
    audit = ART / "04_audits"
    for name in (
        "GATE_A_REPORT.md", "GATE_B_XES_REPORT.md", "GATE_C_REPORT.md", "GATE_D_CONSISTENCY_REPORT.md",
        "JUNYI_DELTAECESTAR_TRACE.csv",
    ):
        src = CORR / "audit" / name
        if src.is_file():
            shutil.copy(src, audit / name)
    (audit / "MODEL_VALIDITY.md").write_text(
        "T-KT masked: causal and padding tests passed (tests/test_protocol_v2.py, 15 passed on 25/10/2026). Primary on ASSISTments.\n"
        "Unmasked T-KT: INVALID for a main claim.\n"
        "DKT pad 0 was not changed.\n"
        "XES3G5M L8: FAIL on the KC-row route. Status DESCRIPTIVE_AUDIT_ONLY. See GATE_B_XES_REPORT.md.\n"
        "Prediction-target alignment for T-KT masked is UT-A5 in tests/test_protocol_v2.py.\n"
        "Multi-KC same-response tests are tests/test_xes_events.py (8 passed). They do not make XES model-eligible.\n",
        encoding="utf-8",
    )
    stats = ART / "05_statistics"
    for folder, names in (
        (CORR / "results", (
            "C_partition_detail.csv", "C_unique_partition_summary.csv", "C_binning_sensitivity.csv",
            "C_size_match_draws.csv.gz", "C_bootstrap_replicates_fold0.csv.gz",
        )),
        (ROOT / "results", (
            "A5_uncertainty_dkt_assist.csv", "A5_secondary_dkt_assist.csv",
            "B1_tktc_uncertainty.csv", "B2_junyi_dkt_uncertainty.csv", "A4_dkt_2x2.csv",
            "results_primary.csv", "results_sensitivity.csv", "results_legacy.csv", "results_invalid.csv",
        )),
    ):
        for name in names:
            src = folder / name
            if src.is_file():
                shutil.copy(src, stats / name)
    write_rebuild()
    blind_stats = scrub_docx(BLIND, ART / "07_submission" / f"{TITLE}_blind.docx")
    scrub_docx(BLIND, BLIND)
    scrub_docx(NAMED, NAMED)
    # Named file must keep the author line in the body. Scrub touched metadata and red only.
    write_submission(blind_stats)
    print("BLIND", blind_stats)
    print("ARTIFACT", ART)


if __name__ == "__main__":
    main()
