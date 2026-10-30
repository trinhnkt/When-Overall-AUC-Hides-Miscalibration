"""Supervisor P-1 checker (NhanXet_P0_IJIET_ban2810_NCS_Trinh_v2.pdf, appendix P-1), transcribed from the PDF.

Run: python -I check_blind.py <blind>.docx
Counts runs with non-empty text and colour FF0000, tracked changes, comments, Author, Last Modified By.
The count of 'P0-BV200' is information only (B2: at most 1, in III.C).
Does not read text inside images (open Fig. 3 separately) and does not check the copyright line.
"""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
z = zipfile.ZipFile(sys.argv[1])
parts = [n for n in z.namelist() if
         re.fullmatch(r"word/(document|footnotes|endnotes|header\d*|footer\d*)\.xml", n)]
red_runs = red_words = red_chars = ins = dele = 0
label = 0
for n in parts:
    root = ET.fromstring(z.read(n))
    ins += len(root.findall(f".//{W}ins"))
    dele += len(root.findall(f".//{W}del"))
    for r in root.iter(f"{W}r"):
        txt = "".join(t.text or "" for t in r.iter(f"{W}t"))
        c = r.find(f"{W}rPr/{W}color")
        if txt.strip() and c is not None and c.get(f"{W}val", "").upper() == "FF0000":
            red_runs += 1
            red_words += len(txt.split())
            red_chars += len(txt)
    label += "".join(t.text or "" for t in root.iter(f"{W}t")).count("P0-BV200")
core = z.read("docProps/core.xml").decode("utf-8")


def tag(name):
    m = re.search(rf"<{name}>(.*?)</{name}>", core)
    return m.group(1) if m else ""


checks = [
    ("Run chữ đỏ (FF0000)", f"{red_runs} run, {red_words} từ, {red_chars} ký tự", red_runs == 0),
    ("Tracked changes (ins + del)", ins + dele, ins + dele == 0),
    ("Có comments.xml", "word/comments.xml" in z.namelist(), "word/comments.xml" not in z.namelist()),
    ("Author", tag("dc:creator"), tag("dc:creator") == ""),
    ("Last Modified By", tag("cp:lastModifiedBy"), tag("cp:lastModifiedBy") == ""),
]
for name, val, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'} {name}: {val}")
print(f"INFO Số lần 'P0-BV200' trong chữ: {label} (B2: tối đa 1, ở III.C)")
print("Lưu ý: script không đọc chữ trong ảnh (kiểm riêng Hình 3) và không kiểm dòng bản quyền (đối chiếu template).")
