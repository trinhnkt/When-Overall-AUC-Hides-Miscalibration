"""Export PDF and .doc from the three A6 clean Word copies with Word (same COM route as a6_verify_clean.py).
Word works in a short temp folder; files are then copied with long-path prefixes. Word's user name is set to
"Anonymous" during the run so the .doc carries no author name, and restored afterwards."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

import win32com.client as w

BASE = r"C:\TRINH\When Overall AUC Hides Miscalibration\When Overall AUC Hides Miscalibration"
NAME = "When Overall AUC Hides Miscalibration - Evaluating Knowledge Tracing on Rarely Practiced Knowledge Components"
CLEAN = BASE + r"\P0_IJIET_FINAL_REVISION_28OCT\a6_clean"
JOBS = [
    (CLEAN + r"\manuscript-pack_manuscript_A6_clean.docx", NAME, BASE + r"\manuscript-pack\output", BASE + r"\manuscript-pack\manuscript"),
    (CLEAN + r"\manuscript-pack_manuscript_blind_A6_clean.docx", NAME + "_blind", BASE + r"\manuscript-pack\output", BASE + r"\manuscript-pack\manuscript"),
    (CLEAN + r"\07_submission_blind_A6_clean.docx", NAME + "_blind", BASE + r"\P0_IJIET_FINAL_CORRECTION_2026\artifact_final\07_submission", None),
]


def long(p: str) -> str:
    p = os.path.abspath(p)
    if not p.startswith("\\\\?\\"):
        return "\\\\?\\" + p
    return p


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    tmp = tempfile.mkdtemp(prefix="export_")
    app = w.Dispatch("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0
    old_user, old_init = app.UserName, app.UserInitials
    app.UserName, app.UserInitials = "Anonymous", "A"
    try:
        for i, (src, out, pdf_dir, doc_dir) in enumerate(JOBS, 1):
            work = os.path.join(tmp, f"in{i}.docx")
            shutil.copyfile(src, work)
            doc = app.Documents.Open(work, ReadOnly=True, AddToRecentFiles=False)
            pages = doc.ComputeStatistics(2)
            pdf = os.path.join(tmp, f"out{i}.pdf")
            doc.ExportAsFixedFormat(pdf, 17)
            dotdoc = None
            if doc_dir:
                dotdoc = os.path.join(tmp, f"out{i}.doc")
                doc.SaveAs2(dotdoc, FileFormat=0, AddToRecentFiles=False)
            doc.Close(False)
            shutil.copyfile(pdf, long(os.path.join(pdf_dir, out + ".pdf")))
            if dotdoc:
                shutil.copyfile(dotdoc, long(os.path.join(doc_dir, out + ".doc")))
            print(f"EXPORTED {out} pages={pages} pdf={os.path.getsize(pdf)}" + (f" doc={os.path.getsize(dotdoc)}" if dotdoc else ""), flush=True)
    finally:
        app.UserName, app.UserInitials = old_user, old_init
        app.Quit()
    print("TEMP", tmp)


if __name__ == "__main__":
    main()
