"""Verify the A6 copies: same text as the red sources, P-1 PASS, Word opens them (temp copy), hyperlink kept."""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import win32com.client as w
from lxml import etree

from msedit import PATHS, W

sys.stdout.reconfigure(encoding="utf-8")
CLEAN = Path("..") / "a6_clean"
NAMES = ["manuscript-pack_manuscript", "manuscript-pack_manuscript_blind", "07_submission_blind"]


def text(path):
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    return "".join(t.text or "" for t in root.iter(W + "t"))


def parts(path):
    with zipfile.ZipFile(path) as z:
        return sorted(z.namelist())


app = w.Dispatch("Word.Application")
app.Visible = False
tmpdir = tempfile.mkdtemp(prefix="a6_verify_")
try:
    for src, name in zip(PATHS, NAMES):
        dest = (CLEAN / f"{name}_A6_clean.docx").resolve()
        same_text = text(src) == text(dest)
        same_parts = parts(src) == parts(dest)
        out = subprocess.run([sys.executable, "check_blind.py", str(dest)], capture_output=True, text=True, encoding="utf-8").stdout
        red_line = [l for l in out.splitlines() if "FF0000" in l]
        tmp = os.path.join(tmpdir, name + ".docx")
        shutil.copy(dest, tmp)
        doc = app.Documents.Open(tmp, ReadOnly=True, AddToRecentFiles=False)
        info = (doc.ComputeStatistics(2), doc.Hyperlinks.Count)
        pdf = os.path.join(tmpdir, name + ".pdf")
        doc.ExportAsFixedFormat(pdf, 17)
        doc.Close(False)
        print(name, "| same text:", same_text, "| same parts:", same_parts, "| pages, links:", info, "| pdf bytes:", os.path.getsize(pdf))
        print("  ", red_line)
finally:
    app.Quit()
    print("temp", tmpdir)
