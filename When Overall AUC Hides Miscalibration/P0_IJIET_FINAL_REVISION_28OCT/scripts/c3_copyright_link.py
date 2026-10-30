"""Make 'CC BY 4.0' in the copyright line a hyperlink, as in IJIET_template.doc. Dry run unless --write."""
from __future__ import annotations

import copy
import os
import sys
import zipfile

from lxml import etree

from msedit import PATHS, W, XML_SPACE, text_of

R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
URL = "https://creativecommons.org/licenses/by/4.0/"
RID = "rIdCCBY40"
TAIL = "CC BY 4.0)."


def main(write: bool) -> None:
    for path in PATHS:
        with zipfile.ZipFile(path) as z:
            items = [(i, z.read(i.filename)) for i in z.infolist()]
        data = {i.filename: b for i, b in items}
        root = etree.fromstring(data["word/document.xml"])
        paras = [p for p in root.iter(W + "p") if text_of(p).startswith("Copyright ©")]
        assert len(paras) == 1, path
        p = paras[0]
        if p.find(W + "hyperlink") is not None:
            print("already linked", path.name)
            continue
        run = p.find(W + "r")
        t = run.find(W + "t")
        assert t.text.endswith(TAIL), t.text[-30:]
        t.text = t.text[: -len(TAIL)]
        t.set(XML_SPACE, "preserve")
        link = etree.Element(W + "hyperlink")
        link.set(R + "id", RID)
        link.set(W + "history", "1")
        lr = copy.deepcopy(run)
        lt = lr.find(W + "t")
        lt.text = "CC BY 4.0"
        link.append(lr)
        tail = copy.deepcopy(run)
        tt = tail.find(W + "t")
        tt.text = ")."
        run.addnext(link)
        link.addnext(tail)
        rels = etree.fromstring(data["word/_rels/document.xml.rels"])
        if not any(r.get("Id") == RID for r in rels):
            rel = etree.SubElement(rels, "{%s}Relationship" % REL_NS)
            rel.set("Id", RID)
            rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink")
            rel.set("Target", URL)
            rel.set("TargetMode", "External")
        if not write:
            print("DRY", path.name)
            continue
        data["word/document.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        data["word/_rels/document.xml.rels"] = etree.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True)
        tmp = path.with_suffix(".docx.tmp")
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for info, _ in items:
                z.writestr(info, data[info.filename])
        os.replace(tmp, path)
        print("UPDATED", path.name)


if __name__ == "__main__":
    main("--write" in sys.argv)
