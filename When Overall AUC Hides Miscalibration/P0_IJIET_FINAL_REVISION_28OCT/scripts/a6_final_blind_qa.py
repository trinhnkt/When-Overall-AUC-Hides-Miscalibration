"""A6: P-1 checks on a .docx, and (after supervisor approval only) a NEW copy with red text set to Automatic.

    py -3 a6_final_blind_qa.py check [path ...]       read-only; defaults to the three manuscript copies
    py -3 a6_final_blind_qa.py clean SRC DEST --approved
        writes DEST (must not exist); red (FF0000) runs in body, tables, headers, footers, footnotes,
        endnotes, and text boxes get w:color w:val="auto"; Author and Last Modified By are blanked.
"""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

from lxml import etree

from msedit import PATHS, W

CP = "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}"
DC = "{http://purl.org/dc/elements/1.1/}"
PARTS = re.compile(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$")
RED = {"FF0000", "ff0000", "C00000", "c00000"}


def red_runs(root) -> int:
    n = 0
    for color in root.iter(W + "color"):
        if color.get(W + "val") in RED and color.getparent().getparent().tag in (W + "r", W + "rPr", W + "pPr"):
            n += 1
    return n


def check(path: Path) -> dict:
    out = {"file": path.name}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        reds = tracked = 0
        text = ""
        for name in names:
            if PARTS.match(name):
                root = etree.fromstring(z.read(name))
                reds += red_runs(root)
                tracked += sum(1 for tag in ("ins", "del", "moveFrom", "moveTo") for _ in root.iter(W + tag))
                text += "".join(t.text or "" for t in root.iter(W + "t"))
        comments = any(n.startswith("word/comments") for n in names)
        core = etree.fromstring(z.read("docProps/core.xml")) if "docProps/core.xml" in names else None
    creator = core.findtext(DC + "creator") if core is not None else None
    modified_by = core.findtext(CP + "lastModifiedBy") if core is not None else None
    out.update({
        "red runs = 0": reds == 0, "red_runs": reds,
        "tracked changes = 0": tracked == 0, "tracked": tracked,
        "comments = False": not comments,
        "Author blank": not (creator or "").strip(), "author": creator,
        "Last Modified By blank": not (modified_by or "").strip(), "last_modified_by": modified_by,
        "P0-BV200 <= 1": text.count("P0-BV200") <= 1, "id_count": text.count("P0-BV200"),
    })
    return out


def clean(src: Path, dest: Path) -> None:
    if dest.exists():
        raise SystemExit(f"{dest} exists; A6 writes a new copy only")
    if src.resolve() == dest.resolve():
        raise SystemExit("source and destination are the same")
    tmp = dest.with_suffix(".tmp.docx")
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if PARTS.match(item.filename):
                root = etree.fromstring(data)
                for color in list(root.iter(W + "color")):
                    if color.get(W + "val") in RED:
                        color.set(W + "val", "auto")
                        for attr in ("themeColor", "themeShade", "themeTint"):
                            color.attrib.pop(W + attr, None)
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            elif item.filename == "docProps/core.xml":
                root = etree.fromstring(data)
                for tag in (DC + "creator", CP + "lastModifiedBy"):
                    el = root.find(tag)
                    if el is not None:
                        el.text = ""
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            zout.writestr(item, data)
    shutil.move(str(tmp), str(dest))
    print("WROTE", dest)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        if "--approved" not in sys.argv:
            raise SystemExit("A6 clean needs --approved after supervisor review of the red changes")
        clean(Path(sys.argv[2]), Path(sys.argv[3]))
        targets = [Path(sys.argv[3])]
    else:
        targets = [Path(p) for p in sys.argv[2:]] or PATHS
    bad = 0
    for path in targets:
        res = check(path)
        print(res["file"])
        for key in ("red runs = 0", "tracked changes = 0", "comments = False", "Author blank", "Last Modified By blank", "P0-BV200 <= 1"):
            print(f"  {'PASS' if res[key] else 'FAIL'} {key}  ({ {k: v for k, v in res.items() if k.islower() and '=' not in k and k != 'file'} if not res[key] else ''})")
            bad += not res[key]
    raise SystemExit(1 if bad else 0)
